"""Repro 06-06: Lost function body (function body → pass).

Defect: A non-trivial function body is replaced with `pass`, losing
all statements.

Root cause: region reduction fails to attribute the function body
blocks to the function's region, leaving an empty body.
"""


def fill_minute_or_day_blank(klines, nowstart, nowend, typet, stocks, forward='pre'):
    if len(klines) == 0:
        return klines
    filled = klines.copy()
    filled.loc[:] = 0
    return filled


def is_same_type(day1, day2, typet):
    if typet == 7:
        return day1.date() == day2.date()
    elif typet == 8:
        return day1.year == day2.year and day1.month == day2.month
    elif typet == 9:
        return day1.year == day2.year
    return False
