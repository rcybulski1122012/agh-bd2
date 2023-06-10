import datetime


def next_month_factory():
    today = datetime.date.today()

    return today + datetime.timedelta(days=30)


datetime_encoders = {
    datetime.date: lambda x: x.isoformat(),
    datetime.datetime: lambda x: x.isoformat(),
}
