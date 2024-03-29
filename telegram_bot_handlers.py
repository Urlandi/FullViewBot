# -*- coding: utf-8 -*-

import logging

import telegram
import resources_messages

from pathlib import Path

from queue import Queue, Empty
from threading import Thread

from subscribers_db import subscriber_start, subscriber_stop
from subscribers_db import subscriber_update, is_subscriber_v4, is_subscriber_v6

from subscribers_db import tablev4_selector_checked, tablev6_selector_checked
from subscribers_db import tablev4_selector_unchecked, tablev6_selector_unchecked
from subscribers_db import get_bgp_table_status, get_subscribers_v4, get_subscribers_v6


def start_cmd(update, context):
    subscriber_id = update.message.from_user.id
    subscriber_start(subscriber_id)

    main_keyboard = telegram.ReplyKeyboardMarkup(resources_messages.main_keyboard_template,
                                                 resize_keyboard=True, one_time_keyboard=True)

    update.message.reply_text(text=resources_messages.start_msg, reply_markup=main_keyboard,
                              parse_mode=telegram.ParseMode.HTML,
                              disable_web_page_preview=True)


def stop_cmd(update, context):
    subscriber_id = update.message.from_user.id
    subscriber_stop(subscriber_id)

    update.message.reply_text(text=resources_messages.stop_msg,
                              parse_mode=telegram.ParseMode.HTML,
                              disable_web_page_preview=True)


def help_cmd(update, context):
    update.message.reply_text(text=resources_messages.help_msg,
                              parse_mode=telegram.ParseMode.HTML,
                              disable_web_page_preview=True)


def switch_keyboard(subscriber_id):
    buttonv4_name = resources_messages.switch_buttonv4_name.format(resources_messages.empty_arrow_left,
                                                                   resources_messages.empty_arrow_right)
    buttonv4_selector = tablev4_selector_checked

    buttonv6_name = resources_messages.switch_buttonv6_name.format(resources_messages.empty_arrow_left,
                                                                   resources_messages.empty_arrow_right)
    buttonv6_selector = tablev6_selector_checked

    if is_subscriber_v4(subscriber_id):
        buttonv4_name = resources_messages.switch_buttonv4_name.format(resources_messages.selected_arrow_left,
                                                                       resources_messages.selected_arrow_right)
        buttonv4_selector = tablev4_selector_unchecked

    if is_subscriber_v6(subscriber_id):
        buttonv6_name = resources_messages.switch_buttonv6_name.format(resources_messages.selected_arrow_left,
                                                                       resources_messages.selected_arrow_right)
        buttonv6_selector = tablev6_selector_unchecked

    buttonv4 = telegram.InlineKeyboardButton(buttonv4_name, callback_data=buttonv4_selector)
    buttonv6 = telegram.InlineKeyboardButton(buttonv6_name, callback_data=buttonv6_selector)

    keyboard_template = [[buttonv4, ],
                         [buttonv6, ], ]

    return telegram.InlineKeyboardMarkup(keyboard_template)


def settings_cmd(update, context):
    if update.message is not None:
        subscriber_id = update.message.from_user.id
        settings_keyboard = switch_keyboard(subscriber_id)
        update.message.reply_text(text=resources_messages.settings_msg,
                                  reply_markup=settings_keyboard,
                                  parse_mode=telegram.ParseMode.HTML,
                                  disable_web_page_preview=True)
    elif update.callback_query is not None:
        subscriber_id = update.callback_query.from_user.id
        subscriber_update(update.callback_query.data, subscriber_id)
        settings_keyboard = switch_keyboard(subscriber_id)
        update.callback_query.message.edit_reply_markup(reply_markup=settings_keyboard)


def echo_cmd(update, context):
    update.message.reply_text(text=resources_messages.echo_msg,
                              parse_mode=telegram.ParseMode.HTML,
                              disable_web_page_preview=True)


def send_status(bot, subscriber_id, message):
    sent = True
    try:
        if isinstance(message, str):
            bot.send_message(chat_id=subscriber_id,
                             text=message,
                             parse_mode=telegram.ParseMode.HTML,
                             disable_web_page_preview=True)
        else:
            bot.send_photo(chat_id=subscriber_id, photo=open(message.name, 'rb'))

    except (telegram.error.Unauthorized,
            telegram.error.BadRequest,
            telegram.error.ChatMigrated) as e:

        logging.info("{:d} sending stopped because - {}".format(subscriber_id, e))
        sent = False

    except telegram.error.TelegramError as e:

        logging.error("{:d} sending skipped because - {}".format(subscriber_id, e))

    except (IOError, FileExistsError, FileNotFoundError, OSError) as e:

        logging.error("{:d} sending file {} skipped because  - {}".format(subscriber_id, message, e))

    return sent


def last_status_cmd(update, context):
    subscriber_id = update.message.from_user.id

    bgp4table_status, bgp6table_status = get_bgp_table_status()

    if is_subscriber_v4(subscriber_id):
        send_status(context.bot, subscriber_id, bgp4table_status)
    if is_subscriber_v6(subscriber_id):
        send_status(context.bot, subscriber_id, bgp6table_status)

    if not is_subscriber_v4(subscriber_id) and not is_subscriber_v6(subscriber_id):
        update.message.reply_text(resources_messages.subscriptions_empty_msg)


def _send_status_queued(bot, subscribers_queue, subscribers_blocked_queue, bgp_status_msg):

    while True:
        subscriber_id = subscribers_queue.get()
        if subscriber_id is not None:
            if not send_status(bot, subscriber_id, bgp_status_msg):
                subscribers_blocked_queue.put(subscriber_id)
            subscribers_queue.task_done()
        else:
            break

    subscribers_queue.put(subscriber_id)
    return subscribers_queue.task_done()


def _update_status_all(bot, subscribers, bgp_status_msg):

    max_threads = 4
    max_subscribes_queue_len = 64

    subscribers_queue = Queue(max_subscribes_queue_len)
    subscribers_blocked_queue = Queue()

    send_threads = set()
    for num_thread in range(max_threads):
        new_send_thread = Thread(target=_send_status_queued,
                                 args=(bot, subscribers_queue, subscribers_blocked_queue, bgp_status_msg))
        send_threads.add(new_send_thread)
        new_send_thread.start()

    for subscriber_id in subscribers:
        subscribers_queue.put(subscriber_id)

    subscribers_queue.join()

    subscribers_queue.put(None)
    for send_thread in send_threads:
        send_thread.join()

    subscribers_blocked = set()
    try:
        while not subscribers_blocked_queue.empty():
            subscribers_blocked.add(subscribers_blocked_queue.get_nowait())
    except Empty:
        pass

    for subscriber_id in subscribers_blocked:
        subscriber_stop(subscriber_id)


def update_status_all_v4(bot, status):
    subscribers_v4 = get_subscribers_v4()
    _update_status_all(bot, subscribers_v4, status)


def update_status_all_v6(bot, status):
    subscribers_v6 = get_subscribers_v6()
    _update_status_all(bot, subscribers_v6, status)


def telegram_error(update, context):
    logging.error("{} - {}".format(update, context.error))
