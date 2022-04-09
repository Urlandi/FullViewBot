# -*- coding: utf-8 -*-
from threading import Timer
from datetime import datetime
from dateutil.relativedelta import relativedelta

from subscribers_db import save_bgp_table_status, update_bgp_table_status
from subscribers_db import subscriber_v4_add, subscriber_v6_add, subscribers_flush

from bgpdump_db import get_bgp_prefixes, plot_bgp_prefixes_length, plot_bgp_prefixes_trend

from telegram_bot import telegram_connect
from telegram_bot_handlers import update_status_all_v4, update_status_all_v6


from db_api import db_connect, db_close, load_subscribers, base_dirname

import logging

repost_task = None


def scheduler(db, bot, bgp_timestamp):

    bgp_timestamp, bgp4_status, bgp6_status = get_bgp_prefixes(bgp_timestamp, db)
    if bgp4_status and bgp6_status:
        update_status_all_v4(bot, bgp4_status)
        update_status_all_v6(bot, bgp6_status)
        save_bgp_table_status(bgp_timestamp, bgp4_status, bgp6_status, db)

    in_an_hour = 3600
    in_four_hour = 4 * in_an_hour

    timenow = round(datetime.now().timestamp())
    date4hour = datetime.fromtimestamp(timenow + in_four_hour)
    day4hour = date4hour.day
    hour4hour = date4hour.hour

    if day4hour == 1 and hour4hour == 0:

        bgp4_plot, bgp6_plot = plot_bgp_prefixes_length()
        if bgp4_plot is not None and bgp6_plot is not None:
            update_status_all_v4(bot, bgp4_plot)
            update_status_all_v6(bot, bgp6_plot)

            bgp4_plot.close()
            bgp6_plot.close()

        last_month = round((date4hour - relativedelta(months=1, hours=1)).timestamp())
        bgp4_plot, bgp6_plot = plot_bgp_prefixes_trend(last_month, db)
        if bgp4_plot is not None and bgp6_plot is not None:
            update_status_all_v4(bot, bgp4_plot)
            update_status_all_v6(bot, bgp6_plot)

            bgp4_plot.close()
            bgp6_plot.close()

    next_start_in = in_an_hour

    internet_wait = 30

    timer_start_at = (timenow // next_start_in + 1) * next_start_in - timenow + internet_wait

    global repost_task
    repost_task = Timer(timer_start_at, scheduler, (db, bot, bgp_timestamp))
    repost_task.start()

    return 0


DONE = 0
STOP_AND_EXIT = 1


def main():

    exit_status_code = DONE

    _logging_file_name = base_dirname + "fullviewbot.log"
    logging.basicConfig(filename=_logging_file_name,
                        level=logging.INFO,
                        format="'%(asctime)s: %(name)s-%(levelname)s: %(message)s'")

    logging.debug("Database opening")
    subscribers_database = db_connect()
    if subscribers_database is None:
        exit_status_code = STOP_AND_EXIT
        return exit_status_code
    logging.debug("Database opened")

    logging.debug("Database status loading")
    bgp_timestamp, bgp4_last_status, bgp6_last_status = update_bgp_table_status(subscribers_database)

    if bgp_timestamp is None or bgp4_last_status is None or bgp6_last_status is None:
        exit_status_code = STOP_AND_EXIT
        return exit_status_code
    logging.debug("Database status loaded")

    logging.debug("Database subscribers loading")
    subscribers_v4 = load_subscribers("IPV4", subscribers_database)
    subscribers_v6 = load_subscribers("IPV6", subscribers_database)

    if subscribers_v4 is None:
        logging.info("Empty v4 subscribers database have been loaded")
    else:
        for subscriber_v4_id in subscribers_v4:
            subscriber_v4_add(subscriber_v4_id)

    if subscribers_v6 is None:
        logging.info("Empty v6 subscribers database have been loaded")
    else:
        for subscriber_v6_id in subscribers_v6:
            subscriber_v6_add(subscriber_v6_id)

    logging.debug("Database subscribers loaded")

    logging.debug("Telegram connecting")
    telegram_job = telegram_connect()
    if telegram_job is None:
        exit_status_code = STOP_AND_EXIT
        return exit_status_code
    logging.debug("Telegram bot started")

    logging.debug("Scheduler job starting")
    if scheduler(subscribers_database, telegram_job.bot, bgp_timestamp) != DONE:
        exit_status_code = STOP_AND_EXIT
        return exit_status_code
    logging.debug("Scheduler job run")

    telegram_job.idle()

    global repost_task
    if repost_task.is_alive():
        repost_task.cancel()

    subscribers_flush(subscribers_database)
    db_close(subscribers_database)

    return exit_status_code


if __name__ == '__main__':
    exit(main())
