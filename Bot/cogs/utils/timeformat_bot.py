import datetime
from typing import List, Union


def indian_standard_time_now() -> List[Union[str, datetime.datetime, int]]:
    ist_date_obj = datetime.timedelta(minutes=30, hours=5)
    ist_time = datetime.datetime.utcnow() + ist_date_obj
    format_time = ist_time.strftime("%a, %#d %B %Y %#I:%M %p")
    return ist_time, format_time, ist_time.timestamp()


def convert_utc_into_ist(utc_date: datetime.datetime) -> List[Union[str, datetime.datetime, int]]:
    ist_date_obj = datetime.timedelta(minutes=30, hours=5)
    ist_time = utc_date + ist_date_obj
    format_time = ist_time.strftime("%a, %#d %B %Y %#I:%M %p")
    return ist_time, format_time, ist_time.timestamp()


if __name__ == '__main__':
    print(indian_standard_time_now())
    print(convert_utc_into_ist(utc_date=datetime.datetime.utcnow()))
