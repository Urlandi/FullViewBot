# -*- coding: utf-8 -*-

from datetime import datetime
import pygal
from pygal.style import Style as PygalStyle
import db_api
import resources_messages
import logging

CHART_WIDTH = 800
CHART_HEIGHT = 600

_bgp4_prefix_chart_name = db_api.base_dirname + "bgp4_prefix_chart.png"
_bgp6_prefix_chart_name = db_api.base_dirname + "bgp6_prefix_chart.png"

_bgp4_prefixes = dict()
_bgp6_prefixes = dict()


def _count_prefixes(prefixes_dump):
    prefixes = dict()
    prefixes_count = 0
    prefix_top_count = 0
    prefix_top = 0
    for prefixes_stat in prefixes_dump.split(';'):
        prefix_cur = prefixes_stat.split(',')
        prefixes[prefix_cur[0]] = prefix_count = int(prefix_cur[1])

        prefixes_count = prefix_count + prefixes_count
        if prefix_top_count <= prefix_count:
            prefix_top_count = prefix_count
            prefix_top = prefix_cur[0]

    return prefixes, prefixes_count, prefix_top_count, prefix_top


def get_bgp_prefixes(timestamp, db):
    bgp_timestamp, bgp4_prefixes_dump, bgp6_prefixes_dump = db_api.load_prefixes(timestamp, db)
    if bgp_timestamp is None or bgp4_prefixes_dump is None or bgp6_prefixes_dump is None:
        return timestamp, db_api.ERROR_STATE, db_api.ERROR_STATE

    ases_timestamp, ases = db_api.load_ases(bgp_timestamp, db)
    if bgp_timestamp != ases_timestamp or ases[0] is None:
        return timestamp, db_api.ERROR_STATE, db_api.ERROR_STATE

    ases_stat_timestat, ases4_prefixes_dump, ases6_prefixes_dump = db_api.load_ases_stat(ases_timestamp, db)
    if ases_stat_timestat != ases_timestamp or ases4_prefixes_dump is None or ases6_prefixes_dump is None:
        return timestamp, db_api.ERROR_STATE, db_api.ERROR_STATE

    bgp4_prefixes, bgp4_prefixes_count, bgp4_prefix_top_count, bgp4_prefix_top = \
        _count_prefixes(bgp4_prefixes_dump)

    global _bgp4_prefixes
    _bgp4_prefixes = dict(sorted(bgp4_prefixes.items(), key=lambda prefix: prefix[1], reverse=True))

    bgp6_prefixes, bgp6_prefixes_count, bgp6_prefix_top_count, bgp6_prefix_top = \
        _count_prefixes(bgp6_prefixes_dump)

    global _bgp6_prefixes
    _bgp6_prefixes = dict(sorted(bgp6_prefixes.items(), key=lambda prefix: prefix[1], reverse=True))

    bgp4_ases_count, bgp6_ases_count, bgp4_ases_only, bgp6_ases_only, bgp4_ases_32, bgp6_ases_32 = ases

    bgp4_status_change = ''
    bgp6_status_change = ''

    since_dump = 36000  # 10 hours
    since_week = 3600 * 24 * 7 + 3600 * 2  # A week with 2 hours

    bgp_timestamp_prev, bgp4_prefixes_dump_prev, bgp6_prefixes_dump_prev = \
        db_api.load_prefixes(bgp_timestamp - since_dump, db, last=False)
    bgp_timestamp_week, bgp4_prefixes_dump_week, bgp6_prefixes_dump_week = \
        db_api.load_prefixes(bgp_timestamp - since_week, db, last=False)

    ases_timestamp_prev, ases_prev = db_api.load_ases(bgp_timestamp_prev, db)
    ases_timestamp_week, ases_week = db_api.load_ases(bgp_timestamp_week, db)

    if (bgp_timestamp_week < bgp_timestamp_prev < bgp_timestamp) and \
            bgp4_prefixes_dump_prev and bgp6_prefixes_dump_prev and \
            bgp4_prefixes_dump_week and bgp6_prefixes_dump_week and \
            (ases_timestamp_week < ases_timestamp_prev < ases_timestamp) and \
            ases_prev and ases_week:

        bgp4_prefixes_prev, bgp4_prefixes_count_prev, bgp4_prefix_top_count_prev, bgp4_prefix_top_prev = \
            _count_prefixes(bgp4_prefixes_dump_prev)

        bgp6_prefixes_prev, bgp6_prefixes_count_prev, bgp6_prefix_top_count_prev, bgp6_prefix_top_prev = \
            _count_prefixes(bgp6_prefixes_dump_prev)

        bgp4_prefixes_week, bgp4_prefixes_count_week, bgp4_prefix_top_count_week, bgp4_prefix_top_week = \
            _count_prefixes(bgp4_prefixes_dump_week)

        bgp6_prefixes_week, bgp6_prefixes_count_week, bgp6_prefix_top_count_week, bgp6_prefix_top_week = \
            _count_prefixes(bgp6_prefixes_dump_week)

        bgp4_change_prev = bgp4_prefixes_count - bgp4_prefixes_count_prev
        bgp6_change_prev = bgp6_prefixes_count - bgp6_prefixes_count_prev

        bgp4_change_week = bgp4_prefixes_count - bgp4_prefixes_count_week
        bgp6_change_week = bgp6_prefixes_count - bgp6_prefixes_count_week

        bgp4_ases_count_prev, bgp6_ases_count_prev = ases_prev[:2]
        bgp4_ases_count_week, bgp6_ases_count_week = ases_week[:2]

        ases4_change_prev = bgp4_ases_count - bgp4_ases_count_prev
        ases6_change_prev = bgp6_ases_count - bgp6_ases_count_prev

        ases4_change_week = bgp4_ases_count - bgp4_ases_count_week
        ases6_change_week = bgp6_ases_count - bgp6_ases_count_week

        bgp4_status_change = resources_messages.bgp_changed_msg.format(bgp4_change_prev,
                                                                       ases4_change_prev,
                                                                       bgp4_change_week,
                                                                       ases4_change_week)
        bgp6_status_change = resources_messages.bgp_changed_msg.format(bgp6_change_prev,
                                                                       ases6_change_prev,
                                                                       ases6_change_week,
                                                                       bgp6_change_week)

    bgp_timestamp_msg = datetime.utcfromtimestamp(bgp_timestamp).strftime("%H:%M %b %d")

    ases4_prefixes, ases4_prefixes_count, ases4_prefix_top_count, ases4_prefix_top = \
        _count_prefixes(ases4_prefixes_dump)
    ases4_prefixes_max = max(list(map(int,ases4_prefixes.keys())))

    ases6_prefixes, ases6_prefixes_count, ases6_prefix_top_count, ases6_prefix_top = \
        _count_prefixes(ases6_prefixes_dump)
    ases6_prefixes_max = max(list(map(int,ases6_prefixes.keys())))

    bgp4_status = resources_messages.bgp4_status_msg.format(
        bgp4_prefixes_count, bgp4_ases_count,
        bgp4_status_change,
        bgp4_prefix_top,
        bgp4_prefix_top_count * 100 / bgp4_prefixes_count,
        bgp4_ases_only * 100 / bgp4_ases_count, bgp4_ases_32 * 100 / bgp4_ases_count,
        ases4_prefix_top_count, ases4_prefix_top, ases4_prefixes_max,
        bgp_timestamp_msg)

    bgp6_status = resources_messages.bgp6_status_msg.format(
        bgp6_prefixes_count, bgp6_ases_count,
        bgp6_status_change,
        bgp6_prefix_top,
        bgp6_prefix_top_count * 100 / bgp6_prefixes_count,
        bgp6_ases_only * 100 / bgp6_ases_count, bgp6_ases_32 * 100 / bgp6_ases_count,
        ases6_prefix_top_count, ases6_prefix_top, ases6_prefixes_max,
        bgp_timestamp_msg)

    return bgp_timestamp, bgp4_status, bgp6_status


def _plot_bgp_prefixes(bgp_prefixes):
    prefix_chart_config = pygal.Config()
    prefix_chart_config.width = CHART_WIDTH
    prefix_chart_config.height = CHART_HEIGHT
    prefix_chart_config.print_values = True
    prefix_chart_config.print_labels = True
    prefix_chart_config.show_legend = False
    prefix_chart_config.style = PygalStyle(value_label_font_size=14, )

    prefixes_chart = pygal.HorizontalBar(prefix_chart_config)

    prefix_length, prefixes_count = zip(*bgp_prefixes.items())
    chart_values_count = 6

    prefixes_sum = sum(prefixes_count)

    sum_other = sum(prefixes_count[chart_values_count:])
    prefixes_chart.add('Other', [{'value': sum_other, 'label': 'Other'}],
                       formatter=lambda value: "{:.1f}%".
                       format(value / prefixes_sum * 100))

    for prefix in reversed(prefix_length[:chart_values_count]):
        prefixes_chart.add(prefix, [{'value': bgp_prefixes[prefix], 'label': '/' + prefix}],
                           formatter=lambda value: "{:.1f}%".
                           format(value / prefixes_sum * 100))

    return prefixes_chart


def plot_bgp_prefixes_length():
    prefixes4_chart = _plot_bgp_prefixes(_bgp4_prefixes)
    prefixes4_chart.title = resources_messages.bgp4_prefix_length_chart_title

    prefixes6_chart = _plot_bgp_prefixes(_bgp6_prefixes)
    prefixes6_chart.title = resources_messages.bgp6_prefix_length_chart_title

    try:
        prefixes4_chart.render_to_png(_bgp4_prefix_chart_name)
        prefixes6_chart.render_to_png(_bgp6_prefix_chart_name)

        bgp4_prefix_chart_file = open(_bgp4_prefix_chart_name, 'rb')
        bgp6_prefix_chart_file = open(_bgp6_prefix_chart_name, 'rb')

    except (IOError, FileExistsError, FileNotFoundError, OSError) as e:
        logging.error("RW chart file error - {}".format(e))
        return db_api.ERROR_STATE, db_api.ERROR_STATE

    return bgp4_prefix_chart_file, bgp6_prefix_chart_file


def _plot_bgp_prefixes_month(bgp_prefixes_history, bgp_prefixes_timestamp):
    prefix_chart_config = pygal.Config()
    prefix_chart_config.width = CHART_WIDTH
    prefix_chart_config.height = CHART_HEIGHT
    prefix_chart_config.show_legend = False
    prefix_chart_config.fill = True
    prefix_chart_config.style = PygalStyle(colors=('Navy',))
    prefix_chart_config.x_labels_major_every = 14
    prefix_chart_config.x_label_rotation = 40
    prefix_chart_config.show_minor_x_labels = False

    prefixes_chart = pygal.Line(prefix_chart_config)

    bgp_prefixes_trend = list()
    for prefixes_dump in bgp_prefixes_history:
        prefixes_count = _count_prefixes(prefixes_dump)[1]
        bgp_prefixes_trend.append(prefixes_count)

    prefixes_chart.add('Prefixes', bgp_prefixes_trend)
    prefixes_chart.x_labels = list(map(lambda timestamp:
                                       datetime.utcfromtimestamp(timestamp).strftime("%b %d %H:%M"),
                                       bgp_prefixes_timestamp))
    return prefixes_chart


def plot_bgp_prefixes_month(period, db):
    bgp_timestamps_history, bgp4_history, bgp6_history = db_api.load_prefixes(period, db, False, True)

    if bgp_timestamps_history is None or bgp4_history is None or bgp6_history is None:
        return db_api.ERROR_STATE, db_api.ERROR_STATE

    date_period = datetime.utcfromtimestamp(bgp_timestamps_history[0])
    monthname = date_period.strftime("%B")
    month = date_period.month

    bgp_timestamps_month = list(filter(lambda timestamp: datetime.utcfromtimestamp(timestamp).month == month,
                                       bgp_timestamps_history))

    month_length = len(bgp_timestamps_month)

    prefixes4_chart = _plot_bgp_prefixes_month(bgp4_history[:month_length], bgp_timestamps_history[:month_length])
    prefixes4_chart.title = resources_messages.bgp4_prefix_trend_chart_title.format(monthname)

    prefixes6_chart = _plot_bgp_prefixes_month(bgp6_history[:month_length], bgp_timestamps_history[:month_length])
    prefixes6_chart.title = resources_messages.bgp6_prefix_trend_chart_title.format(monthname)

    try:
        prefixes4_chart.render_to_png(_bgp4_prefix_chart_name)
        prefixes6_chart.render_to_png(_bgp6_prefix_chart_name)

        bgp4_prefix_chart_file = open(_bgp4_prefix_chart_name, 'rb')
        bgp6_prefix_chart_file = open(_bgp6_prefix_chart_name, 'rb')

    except (IOError, FileExistsError, FileNotFoundError, OSError) as e:
        logging.error("RW chart file error - {}".format(e))
        return db_api.ERROR_STATE, db_api.ERROR_STATE

    return bgp4_prefix_chart_file, bgp6_prefix_chart_file


def _plot_bgp_ases_month(bgp_ases_history, bgp_second_ases_history, bgp_ases_timestamp):
    ases_chart_config = pygal.Config()
    ases_chart_config.width = CHART_WIDTH
    ases_chart_config.height = CHART_HEIGHT
    ases_chart_config.show_legend = False
    ases_chart_config.fill = True
    ases_chart_config.style = PygalStyle(colors=('Gold', 'Green',))
    ases_chart_config.x_labels_major_every = 14
    ases_chart_config.x_label_rotation = 40
    ases_chart_config.show_minor_x_labels = False

    ases_chart = pygal.Line(ases_chart_config)

    ases_chart.add('ASes', bgp_ases_history)
    # ases_chart.add('Only ASes', bgp_second_ases_history, secondary=True, fill=False)
    ases_chart.x_labels = list(map(lambda timestamp:
                                   datetime.utcfromtimestamp(timestamp).strftime("%b %d %H:%M"),
                                   bgp_ases_timestamp))
    return ases_chart


def plot_bgp_ases_month(period, db):
    bgp_timestamps_history, ases_history = db_api.load_ases(period, db, False, True)

    if bgp_timestamps_history is None or ases_history[0] is None:
        return db_api.ERROR_STATE, db_api.ERROR_STATE

    date_period = datetime.utcfromtimestamp(bgp_timestamps_history[0])
    monthname = date_period.strftime("%B")
    month = date_period.month

    bgp_timestamps_month = list(filter(lambda timestamp: datetime.utcfromtimestamp(timestamp).month == month,
                                       bgp_timestamps_history))

    month_length = len(bgp_timestamps_month)

    bgp4_ases_history = list(map(lambda ases_dump: ases_dump[0], ases_history))
    bgp4_only_ases_history = list(map(lambda ases_dump: ases_dump[2], ases_history))
    ases4_chart = _plot_bgp_ases_month(bgp4_ases_history[:month_length], bgp4_only_ases_history[:month_length],
                                       bgp_timestamps_history[:month_length])
    ases4_chart.title = resources_messages.bgp4_ases_trend_chart_title.format(monthname)

    bgp6_ases_history = list(map(lambda ases_dump: ases_dump[1], ases_history))
    bgp6_only_ases_history = list(map(lambda ases_dump: ases_dump[3], ases_history))
    ases6_chart = _plot_bgp_ases_month(bgp6_ases_history[:month_length], bgp6_only_ases_history[:month_length],
                                       bgp_timestamps_history[:month_length])
    ases6_chart.title = resources_messages.bgp6_ases_trend_chart_title.format(monthname)

    try:
        ases4_chart.render_to_png(_bgp4_prefix_chart_name)
        ases6_chart.render_to_png(_bgp6_prefix_chart_name)

        bgp4_prefix_chart_file = open(_bgp4_prefix_chart_name, 'rb')
        bgp6_prefix_chart_file = open(_bgp6_prefix_chart_name, 'rb')

    except (IOError, FileExistsError, FileNotFoundError, OSError) as e:
        logging.error("RW chart file error - {}".format(e))
        return db_api.ERROR_STATE, db_api.ERROR_STATE

    return bgp4_prefix_chart_file, bgp6_prefix_chart_file
