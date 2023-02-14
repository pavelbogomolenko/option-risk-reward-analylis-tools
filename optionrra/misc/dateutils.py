from datetime import datetime, date, timedelta
from functools import partial


def daterange(d_from: date, d_to: date):
    days_delta = d_to - d_from
    for n in range(int(days_delta.days) + 1):
        yield d_from + timedelta(n)


def num_workdays_between(d_from: date, d_to: date) -> int:
    work_days = 0
    for d in daterange(d_from, d_to):
        if d.weekday() not in [5, 6]:
            work_days += 1
    return work_days


num_workdays_until = partial(num_workdays_between, datetime.now())
