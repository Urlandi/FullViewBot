# -*- coding: utf-8 -*-

import sqlite3 as db_api
import logging

import os
from sys import argv

SUBSCRIBERS_DATABASE_NAME = "subscribers.sqlite3"

ERROR_STATE = None
SUCCESS_STATE = 0

base_dirname = os.path.abspath(os.path.dirname(argv[0])) + "/"

_database_global_handler = None


def db_connect(db_name=base_dirname+SUBSCRIBERS_DATABASE_NAME):

    try:
        db = db_api.connect(db_name, check_same_thread=False)
    except db_api.DatabaseError as e:
        logging.critical("Database open error - {}".format(e))
        return None

    global _database_global_handler
    _database_global_handler = db

    return _database_global_handler


def save_bgp_table_status(bgp_timestamp, bgp4table_status, bgp6table_status, subscribers_db=None):

    if subscribers_db is None:
        if _database_global_handler is None:
            return ERROR_STATE
        else:
            db = _database_global_handler
    else:
        db = subscribers_db

    if bgp4table_status is None or bgp6table_status is None:
        return ERROR_STATE

    db_query = "UPDATE status SET DUMP_TIME = {:d}, IPV4_TEXT = '{:s}', IPV6_TEXT = '{:s}'".format(
        bgp_timestamp, bgp4table_status, bgp6table_status)

    try:
        db_cursor = db.cursor()
        db_cursor.execute(db_query)
        db.commit()

    except db_api.DatabaseError as e:
        db.rollback()
        logging.critical("Database update error - {}".format(e))
        return ERROR_STATE

    return SUCCESS_STATE


def load_bgp_table_status(subscribers_db=None):

    if subscribers_db is None:
        if _database_global_handler is None:
            return ERROR_STATE
        else:
            db = _database_global_handler
    else:
        db = subscribers_db

    statuses_fields = ("status.DUMP_TIME", "status.IPV4_TEXT", "status.IPV6_TEXT")

    db_query = "SELECT {} FROM status LIMIT 1".format(",".join(statuses_fields))

    try:
        db_cursor = db.cursor()
        db_cursor.execute(db_query)

        statuses = db_cursor.fetchone()

    except db_api.DatabaseError as e:
        logging.critical("Database select error - {}".format(e))
        return ERROR_STATE, ERROR_STATE, ERROR_STATE

    if statuses is None or len(statuses) == 0:
        logging.critical("Database BGP statuses returned empty data")
        return ERROR_STATE, ERROR_STATE, ERROR_STATE

    bgp_timestamp = statuses[0]
    bgp4_status = statuses[1]
    bgp6_status = statuses[2]

    return bgp_timestamp, bgp4_status, bgp6_status


def save_subscriber(is_subscriber_v4, is_subscriber_v6, subscriber_id, subscribers_db=None):

    if subscribers_db is None:
        if _database_global_handler is None:
            return ERROR_STATE
        else:
            db = _database_global_handler
    else:
        db = subscribers_db

    db_query_insert = "INSERT INTO subscribers(subscriber_id, IPV4, IPV6) VALUES({:d},{:d},{:d})".format(
        subscriber_id,
        is_subscriber_v4,
        is_subscriber_v6)

    db_query = "UPDATE subscribers SET subscriber_id = {0:d}, IPV4 = {1:d}, IPV6 = {2:d} \
    WHERE subscriber_id={0:d}" .format(
        subscriber_id,
        is_subscriber_v4,
        is_subscriber_v6)

    subscriber_exist = False

    db_cursor = db.cursor()

    try:
        db_cursor.execute(db_query_insert)
        db.commit()
    except db_api.IntegrityError:
        db.rollback()
        subscriber_exist = True
    except db_api.DatabaseError as e:
        db.rollback()
        logging.critical("Database insert error - {}".format(e))
        return ERROR_STATE

    if subscriber_exist:
        try:
            db_cursor.execute(db_query)
            db.commit()
        except db_api.DatabaseError as e:
            db.rollback()
            logging.critical("Database update error - {}".format(e))
            return ERROR_STATE

    return SUCCESS_STATE


def delete_subscriber(subscriber_id, subscribers_db=None):

    if subscribers_db is None:
        if _database_global_handler is None:
            return ERROR_STATE
        else:
            db = _database_global_handler
    else:
        db = subscribers_db

    db_query = "DELETE FROM subscribers WHERE subscriber_id={:d}" .format(subscriber_id)

    try:
        db_cursor = db.cursor()
        db_cursor.execute(db_query)
        db.commit()
    except db_api.DatabaseError as e:
        db.rollback()
        logging.critical("Database subscriber delete error - {}".format(e))
        return ERROR_STATE

    return SUCCESS_STATE


def save_subscribers(subscribers_v4, subscribers_v6, subscribers_db=None):

    if subscribers_db is None:
        if _database_global_handler is None:
            return ERROR_STATE
        else:
            db = _database_global_handler
    else:
        db = subscribers_db

    save_complete_status = SUCCESS_STATE
    subscribers = set().union(subscribers_v4, subscribers_v6)

    for subscriber_id in subscribers:
        is_subscriber_v4 = subscriber_id in subscribers_v4
        is_subscriber_v6 = subscriber_id in subscribers_v4

        if save_subscriber(is_subscriber_v4,
                           is_subscriber_v6,
                           subscriber_id, db) != SUCCESS_STATE:
            save_complete_status = ERROR_STATE

    return save_complete_status


def load_subscribers(table_type, subscribers_db=None):

    if subscribers_db is None:
        if _database_global_handler is None:
            return ERROR_STATE
        else:
            db = _database_global_handler
    else:
        db = subscribers_db

    db_query = "SELECT subscribers.subscriber_id FROM subscribers \
WHERE subscribers.{:s} = 1".format(table_type)

    try:
        db_cursor = db.cursor()
        db_cursor.execute(db_query)

        subscribers = db_cursor.fetchall()

    except db_api.DatabaseError as e:
        logging.critical("Database select error - {}".format(e))
        return ERROR_STATE

    if subscribers is None or len(subscribers) == 0:
        logging.critical("Database subscribers returned empty data")
        return ERROR_STATE

    subscriber_ids, = zip(*subscribers)

    return set(subscriber_ids)


def db_close(subscribers_db):

    if subscribers_db is not None:
        subscribers_db.commit()
        subscribers_db.close()


def load_prefixes(timestamp=0, subscribers_db=None, last=True, trend=False):

    if subscribers_db is None:
        if _database_global_handler is None:
            return ERROR_STATE
        else:
            db = _database_global_handler
    else:
        db = subscribers_db

    prefixes_fields = ("prefixes.DUMP_TIME", "prefixes.IPV4", "prefixes.IPV6")

    if last:
        order = 'DESC'
    else:
        order = 'ASC'

    db_query = "SELECT {:s} FROM prefixes WHERE prefixes.DUMP_TIME > {:d} " \
               "ORDER BY prefixes.DUMP_TIME {:s}".format(",".join(prefixes_fields), timestamp, order)

    if trend is False:
        db_query = db_query + ' LIMIT 1'

    try:
        db_cursor = db.cursor()
        db_cursor.execute(db_query)

        if trend:
            prefixes = db_cursor.fetchall()
        else:
            prefixes = db_cursor.fetchone()

    except db_api.DatabaseError as e:
        logging.critical("Database select error - {}".format(e))
        return timestamp, ERROR_STATE, ERROR_STATE

    if prefixes is None or len(prefixes) == 0:
        # logging.critical("Database BGP statuses returned empty data")
        return timestamp, ERROR_STATE, ERROR_STATE

    if trend:
        bgp_timestamp = list()
        bgp4_prefixes = list()
        bgp6_prefixes = list()

        for dump_trend in prefixes:
            bgp_timestamp.append(dump_trend[0])
            bgp4_prefixes.append(dump_trend[1])
            bgp6_prefixes.append(dump_trend[2])
    else:
        bgp_timestamp = prefixes[0]
        bgp4_prefixes = prefixes[1]
        bgp6_prefixes = prefixes[2]

    return bgp_timestamp, bgp4_prefixes, bgp6_prefixes


def load_ases(timestamp, subscribers_db=None, last=True, trend=False):

    if subscribers_db is None:
        if _database_global_handler is None:
            return ERROR_STATE
        else:
            db = _database_global_handler
    else:
        db = subscribers_db

    ases_fields = ("ases.DUMP_TIME",
                   "ases.ASNV4", "ases.ASNV6",
                   "ases.ASNV4_ONLY", "ases.ASNV6_ONLY",
                   "ases.ASNV4_32", "ases.ASNV6_32")

    if last:
        order = 'DESC'
    else:
        order = 'ASC'

    db_query = "SELECT {:s} FROM ases WHERE ases.DUMP_TIME > {:d} " \
               "ORDER BY ases.DUMP_TIME {:s}".format(",".join(ases_fields), timestamp, order)

    if trend is False:
        db_query = "SELECT {:s} FROM ases WHERE ases.DUMP_TIME = {:d} LIMIT 1".format(",".join(ases_fields), timestamp)

    try:
        db_cursor = db.cursor()
        db_cursor.execute(db_query)

        if trend:
            ases = db_cursor.fetchall()
        else:
            ases = db_cursor.fetchone()

    except db_api.DatabaseError as e:
        logging.critical("Database select error - {}".format(e))
        return timestamp, (ERROR_STATE,)

    if ases is None or len(ases) == 0:
        # logging.critical("Database BGP statuses returned empty data")
        return timestamp, (ERROR_STATE,)

    if trend:
        bgp_timestamp = list()
        ases_status = list()

        for dump_trend in ases:
            bgp_timestamp.append(dump_trend[0])
            ases_dump = list()
            for ases_trend in dump_trend[1:]:
                ases_dump.append(ases_trend)

            ases_status.append(ases_dump)
    else:
        bgp_timestamp = ases[0]
        ases_status = ases[1:]

    return bgp_timestamp, ases_status
