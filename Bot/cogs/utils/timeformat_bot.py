import datetime


def indian_standard_time_now(hrs=5, mins=30):
    total_time = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=hrs, minutes=mins), "IST"))
    format_time = total_time.strftime("%a, %#d %B %Y %#I:%M %p")
    auto_time = datetime.datetime(year=total_time.year, month=total_time.month, day=total_time.day, hour=total_time.hour, minute=total_time.minute, second=total_time.second)
    return auto_time, format_time, auto_time.timestamp()


def convert_utc_into_ist(utc_date: datetime.datetime):
    ist_date_obj = datetime.timedelta(minutes=30, hours=5)
    ist_time = utc_date + ist_date_obj
    format_time = ist_time.strftime("%a, %#d %B %Y %#I:%M %p")
    return ist_time, format_time


if __name__ == '__main__':
    print(convert_utc_into_ist(utc_date=datetime.datetime.utcnow())[1])
