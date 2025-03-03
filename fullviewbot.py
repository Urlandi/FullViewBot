# -*- coding: utf-8 -*-
from threading import Timer
from datetime import datetime
from dateutil.relativedelta import relativedelta

from subscribers_db import save_bgp_table_status, update_bgp_table_status
from subscribers_db import subscriber_v4_add, subscriber_v6_add, subscribers_flush

from bgpdump_db import get_bgp_prefixes, plot_bgp_prefixes_length, plot_bgp_prefixes_month, plot_bgp_ases_month
from bgpdump_db import plot_bgp_prefixes_year, plot_bgp_ases_year

from telegram_bot import telegram_connect
from telegram_bot_handlers import update_status_all_v4, update_status_all_v6, get_task_threads


from db_api import db_connect, db_close, load_subscribers, base_dirname

import logging

repost_task = None
repost_task_cancel = False


def scheduler(db, bot, status_timestamp):
   
    global repost_task
    global repost_task_cancel

    if repost_task_cancel:
        repost_task = None
        return 0

    timenow = datetime.now()
    timestampnow = round(timenow.timestamp())

    in_an_hour = 60 * 60
    next_start_in = in_an_hour

    internet_wait = 30

    timer_start_at = (timestampnow // next_start_in + 1) * next_start_in - timestampnow + internet_wait

    repost_task = Timer(timer_start_at, scheduler, (db, bot, bgp_timestamp))
    repost_task.start()

    bgp_timestamp, bgp4_status, bgp6_status = get_bgp_prefixes(status_timestamp, db)    

    if bgp4_status and bgp6_status:
        update_status_all_v4(bot, bgp4_status)
        update_status_all_v6(bot, bgp6_status)
        save_bgp_table_status(bgp_timestamp, bgp4_status, bgp6_status, db)

        prefix_length_schedule_day = 1
        prefix_length_schedule_hour = 12

        if timenow.weekday() == prefix_length_schedule_day and timenow.hour == prefix_length_schedule_hour:
            bgp4_plot, bgp6_plot = plot_bgp_prefixes_length()
            if bgp4_plot is not None and bgp6_plot is not None:
                update_status_all_v4(bot, bgp4_plot)
                update_status_all_v6(bot, bgp6_plot)

                bgp4_plot.close()
                bgp6_plot.close()

    prefix_history_scheduler_day = 1
    prefix_history_scheduler_hour = 16

    if timenow.day == prefix_history_scheduler_day and timenow.hour == prefix_history_scheduler_hour:

        prev_month_date = timenow - relativedelta(days=10)

        last_month = round(datetime(prev_month_date.year, prev_month_date.month, 1).timestamp())

        bgp4_plot, bgp6_plot = plot_bgp_prefixes_month(last_month, db)
        if bgp4_plot is not None and bgp6_plot is not None:
            update_status_all_v4(bot, bgp4_plot)
            update_status_all_v6(bot, bgp6_plot)

            bgp4_plot.close()
            bgp6_plot.close()

        bgp4_plot, bgp6_plot = plot_bgp_ases_month(last_month, db)
        if bgp4_plot is not None and bgp6_plot is not None:
            update_status_all_v4(bot, bgp4_plot)
            update_status_all_v6(bot, bgp6_plot)

            bgp4_plot.close()
            bgp6_plot.close()

    annual_history_scheduler_month = 1
    
    if timenow.day == prefix_history_scheduler_day and timenow.hour == prefix_history_scheduler_hour and timenow.month == annual_history_scheduler_month:
        
        last_year = round(datetime(prev_month_date.year, 1, 1).timestamp())

        bgp4_plot, bgp6_plot = plot_bgp_prefixes_year(last_year, db)
        if bgp4_plot is not None and bgp6_plot is not None:
            update_status_all_v4(bot, bgp4_plot)
            update_status_all_v6(bot, bgp6_plot)

            bgp4_plot.close()
            bgp6_plot.close()

        bgp4_plot, bgp6_plot = plot_bgp_ases_year(last_year, db)
        if bgp4_plot is not None and bgp6_plot is not None:
            update_status_all_v4(bot, bgp4_plot)
            update_status_all_v6(bot, bgp6_plot)

            bgp4_plot.close()
            bgp6_plot.close()    

    return 0

DONE = 0
STOP_AND_EXIT = 1


def main():

    exit_status_code = DONE

    _logging_file_name = base_dirname + "fullviewbot.log"
    logging.basicConfig(filename=_logging_file_name,
                        level=logging.INFO,
                        format="'%(asctime)s: %(name)s-%(levelname)s: %(message)s'")
    logging.getLogger("httpx").setLevel(logging.WARNING)

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

    global repost_task

    logging.debug("Scheduler job starting")
    try:
        first_start_in = 5
        repost_task = Timer(first_start_in, scheduler, (subscribers_database, telegram_job.updater.bot, bgp_timestamp))
        repost_task.start()
    except RuntimeError as e:
         logging.fatal("Scheduler job didn't start - {}".format(e))
         return STOP_AND_EXIT                            
    logging.debug("Scheduler job run")

    telegram_job.post_init = get_task_threads    
    telegram_job.run_polling(drop_pending_updates=True)
    
    global repost_task_cancel
    repost_task_cancel = True    
    
    if repost_task is not None and repost_task.is_alive():
        repost_task.cancel()

    subscribers_flush(subscribers_database)
    db_close(subscribers_database)

    return exit_status_code


if __name__ == '__main__':
    exit(main())
