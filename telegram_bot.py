# -*- coding: utf-8 -*-

from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler
from telegram.ext.filters import ALL as FilterAll, MessageFilter
from telegram.error import TelegramError

from config_telegram_auth import TOKEN
from telegram_bot_handlers import start_cmd, stop_cmd, settings_cmd, help_cmd, echo_cmd, last_status_cmd
from telegram_bot_handlers import telegram_error
from resources_messages import keyboard_buttons_name

import logging


class FilterLastStatus(MessageFilter):
    def filter(self, message):
        return keyboard_buttons_name["last_status_name"] == message.text


class FilterSettings(MessageFilter):
    def filter(self, message):
        return keyboard_buttons_name["settings_name"] == message.text


class FilterHelp(MessageFilter):
    def filter(self, message):
        return keyboard_buttons_name["help_name"] == message.text

MAX_CONNECTIONS_POOL = 120
MAX_CONCURRENT_UPDATES = 1

def telegram_connect():

    try:
        application = ApplicationBuilder().token(TOKEN).pool_timeout(MAX_CONNECTIONS_POOL).concurrent_updates(MAX_CONCURRENT_UPDATES).build()
        application.add_error_handler(telegram_error)

        application.add_handler(CommandHandler("start", start_cmd))
        application.add_handler(CommandHandler("stop", stop_cmd))

        application.add_handler(CommandHandler("help", help_cmd))
        application.add_handler(MessageHandler(FilterHelp(), help_cmd))

        application.add_handler(CommandHandler("settings", settings_cmd))
        application.add_handler(MessageHandler(FilterSettings(), settings_cmd))
        application.add_handler(CallbackQueryHandler(settings_cmd))

        application.add_handler(CommandHandler("status", last_status_cmd))
        application.add_handler(MessageHandler(FilterLastStatus(), last_status_cmd))

        application.add_handler(MessageHandler(FilterAll, echo_cmd)) 

    except TelegramError as e:
        logging.fatal("Can't connect to telegram - {}".format(e))
        return None

    return application
