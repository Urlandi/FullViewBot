# -*- coding: utf-8 -*-
import asyncio
import logging
import time

import telegram
import resources_messages

from pathlib import Path

from subscribers_db import subscriber_start, subscriber_stop
from subscribers_db import subscriber_update, is_subscriber_v4, is_subscriber_v6

from subscribers_db import tablev4_selector_checked, tablev6_selector_checked
from subscribers_db import tablev4_selector_unchecked, tablev6_selector_unchecked
from subscribers_db import get_bgp_table_status, get_subscribers_v4, get_subscribers_v6

_update_task_threads = None

MAX_UPDATE_QUEUE = 5
WAIT_TIME = 2


async def get_task_threads(application):
    global _update_task_threads
    _update_task_threads = asyncio.get_event_loop()


async def start_cmd(update, context):
    subscriber_id = update.message.from_user.id
    subscriber_start(subscriber_id)

    main_keyboard = telegram.ReplyKeyboardMarkup(resources_messages.main_keyboard_template,
                                                 resize_keyboard=True, one_time_keyboard=True)

    await update.message.reply_text(text=resources_messages.start_msg, reply_markup=main_keyboard,
                              parse_mode=telegram.constants.ParseMode.HTML,
                              disable_web_page_preview=True)


async def stop_cmd(update, context):
    subscriber_id = update.message.from_user.id
    subscriber_stop(subscriber_id)

    await update.message.reply_text(text=resources_messages.stop_msg,
                              parse_mode=telegram.constants.ParseMode.HTML,
                              disable_web_page_preview=True)


async def help_cmd(update, context):
    await update.message.reply_text(text=resources_messages.help_msg,
                              parse_mode=telegram.constants.ParseMode.HTML,
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


async def settings_cmd(update, context):
    if update.message is not None:
        subscriber_id = update.message.from_user.id
        settings_keyboard = switch_keyboard(subscriber_id)
        await update.message.reply_text(text=resources_messages.settings_msg,
                                  reply_markup=settings_keyboard,
                                  parse_mode=telegram.constants.ParseMode.HTML,
                                  disable_web_page_preview=True)
    elif update.callback_query is not None:
        subscriber_id = update.callback_query.from_user.id
        subscriber_update(update.callback_query.data, subscriber_id)
        settings_keyboard = switch_keyboard(subscriber_id)
        await update.callback_query.message.edit_reply_markup(reply_markup=settings_keyboard)


async def echo_cmd(update, context):
    await update.message.reply_text(text=resources_messages.echo_msg,
                              parse_mode=telegram.constants.ParseMode.HTML,
                              disable_web_page_preview=True)


async def send_status(bot, subscriber_id, message):
    sent = True
    try:
        if isinstance(message, str):
            await bot.send_message(chat_id=subscriber_id,
                             text=message,
                             parse_mode=telegram.constants.ParseMode.HTML,
                             disable_web_page_preview=True)
        else:
            await bot.send_photo(chat_id=subscriber_id, photo=open(message.name, 'rb'))

    except (telegram.error.Forbidden,
            telegram.error.BadRequest,
            telegram.error.ChatMigrated) as e:

        logging.info("{:d} sending stopped because - {}".format(subscriber_id, e))
        sent = False

    except telegram.error.TelegramError as e:

        logging.error("{:d} sending skipped because - {}".format(subscriber_id, e))

    except (IOError, FileExistsError, FileNotFoundError, OSError) as e:

        logging.error("{:d} sending file {} skipped because  - {}".format(subscriber_id, message, e))

    return sent


async def last_status_cmd(update, context):
    subscriber_id = update.message.from_user.id

    bgp4table_status, bgp6table_status = get_bgp_table_status()

    if is_subscriber_v4(subscriber_id):
        await send_status(context.bot, subscriber_id, bgp4table_status)
    if is_subscriber_v6(subscriber_id):
        await send_status(context.bot, subscriber_id, bgp6table_status)

    if not is_subscriber_v4(subscriber_id) and not is_subscriber_v6(subscriber_id):
        await update.message.reply_text(resources_messages.subscriptions_empty_msg)


async def _send_status_queued(bot, subscriber_id, bgp_status_msg):

    if subscriber_id is not None:
        if not await send_status(bot, subscriber_id, bgp_status_msg):
            subscriber_stop(subscriber_id)
        

def _update_status_all(bot, subscribers, bgp_status_msg):

    global _update_task_threads
    if _update_task_threads is None:
        logging.fatal("Scheduler fatal, no spinning")
        return

    send_threads = set()
    for subscriber_id in subscribers:
        new_send_thread = _update_task_threads.create_task(_send_status_queued(bot, subscriber_id, bgp_status_msg))     
        new_send_thread.add_done_callback(send_threads.discard)
        send_threads.add(new_send_thread)
          
        if len(send_threads) % MAX_UPDATE_QUEUE == 0:
            time.sleep(WAIT_TIME)


def update_status_all_v4(bot, status):
    subscribers_v4 = get_subscribers_v4()
    _update_status_all(bot, subscribers_v4, status)


def update_status_all_v6(bot, status):
    subscribers_v6 = get_subscribers_v6()
    _update_status_all(bot, subscribers_v6, status)


async def telegram_error(update, context):
    logging.error("{} - {}".format(update, context.error))
