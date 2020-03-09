# encoding: utf-8
import time
from datetime import datetime, tzinfo, timedelta
from tzlocal import get_localzone


def timestamp(date=None):
    if date is None:
        t = time.time()
    else:
        time_array = date.timetuple()
        # time_array = date.utctimetuple()
        t = time.mktime(time_array)
    return int(round(t * 1000))


def time_now_str():
    now = datetime.now(tz=get_localzone())
    return now.strftime("%Y-%m-%d %H:%M:%S.%f%z")


def date_with_format(date_string, date_format):
    return datetime.strptime(date_string, date_format)


def timestamp_with_month(year, month, timezone):
    local_tm = datetime.fromtimestamp(0)
    utc_tm = datetime.utcfromtimestamp(0)
    offset = local_tm - utc_tm

    _date = datetime(year=year, month=month, day=1)
    _date = _date - timedelta(hours=timezone) + offset
    _timestamp = timestamp(date=_date)
    return _timestamp


"""
tzinfo是关于时区信息的类
tzinfo是一个抽象类，所以不能直接被实例化
"""


class UTC(tzinfo):
    """UTC"""

    def __init__(self, offset=0):
        self._offset = offset

    def utcoffset(self, dt):
        return timedelta(hours=self._offset)

    def tzname(self, dt):
        return "UTC +%s" % self._offset

    def dst(self, dt):
        return timedelta(hours=self._offset)
