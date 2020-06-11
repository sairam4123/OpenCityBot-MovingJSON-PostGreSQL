import datetime
from typing import Tuple


def indian_standard_time_now() -> Tuple[datetime.datetime, str, float]:
    ist_date_obj = datetime.timedelta(minutes=30, hours=5)
    ist_time = datetime.datetime.utcnow() + ist_date_obj
    format_time = ist_time.strftime("%a, %#d %B %Y %#I:%M %p")
    return ist_time, format_time, ist_time.timestamp()


def convert_utc_into_ist(utc_date: datetime.datetime) -> Tuple[datetime.datetime, str, float]:
    ist_date_obj = datetime.timedelta(minutes=30, hours=5)
    ist_time = utc_date + ist_date_obj
    format_time = ist_time.strftime("%a, %#d %B %Y %#I:%M %p")
    return ist_time, format_time, ist_time.timestamp()


def format_duration(seconds: float) -> str:
    times = ["year", "month", "day", "hour", "minute", "second"]
    if seconds == 0:
        return "now"
    else:
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)
        mo, d = divmod(d, 30)
        y, mo = divmod(mo, 12)
        time = [y, mo, d, h, m, s]  # [year, day, hour, ...]
        readable_time = []
        la = list(zip(time, times))  # [(y,"year"),(d,"day")...]
        for i in la:
            t, ts = i  # t=y ts=year , t=d, ts=day...
            if t:
                t_s = [ts if t == 1 else ts + "s"]  # year or +"s"
                readable_time_str = " " + str(int(t)) + " " + "".join(t_s)  # y year/s  d day/s
                readable_time.append(readable_time_str)  # ["y year/s", "d day/s", ...]
        if len(readable_time) == 1:
            return ("".join(readable_time)).strip()
        else:
            return (",".join(readable_time[:-1]) + " and" + "".join(readable_time[-1])).strip()


def datetime_to_seconds(date_time_1: datetime.datetime) -> float:
    date_time = indian_standard_time_now()[0] - date_time_1
    seconds = date_time.total_seconds()
    return seconds


if __name__ == '__main__':
    print(indian_standard_time_now())
    print(convert_utc_into_ist(utc_date=datetime.datetime.utcnow()))
