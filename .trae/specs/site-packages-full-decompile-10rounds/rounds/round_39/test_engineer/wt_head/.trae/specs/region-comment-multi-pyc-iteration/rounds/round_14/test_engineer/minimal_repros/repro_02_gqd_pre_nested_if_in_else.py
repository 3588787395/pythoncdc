"""R14 DEFECT-REPRO 02: get_qry_date `pre` branch — nested if-in-else + inner if/else.

Pattern (mirrors tools.pyc get_qry_date, date_type=='pre' else-branch):
    else:
        if len(date) == 8:
            date = date_str_type_change(...)
        if date >= now:
            day = now
            if not is_trading_day(day):     # inner if/else
                date = get_trade_days(...)[0]
            else:
                date = get_trade_days(..., count=2)[0]
        else:
            day = date
            date = get_trade_days(...)[0]

Adds an inner if/else inside the second sequential if, deepening the nesting
and exposing the flattening + jump-target renumbering mismatch.
"""
import datetime


def get_qry_date_pre(now, date=None, date_type='pre'):
    if date_type == 'pre':
        if date is None:
            day = now
            if not is_trading_day(day):
                date = get_trade_days(end_date=day, count=1)[0]
            else:
                date = get_trade_days(end_date=day, count=2)[0]
        elif isinstance(date, datetime.date):
            date = date.strftime('%Y-%m-%d')
        else:
            if len(date) == 8:
                date = date_str_type_change(date, '%Y%m%d', '%Y-%m-%d')
            if date >= now:
                day = now
                if not is_trading_day(day):
                    date = get_trade_days(end_date=day, count=1)[0]
                else:
                    date = get_trade_days(end_date=day, count=2)[0]
            else:
                day = date
                date = get_trade_days(end_date=day, count=1)[0]
        return date
    return date


def date_str_type_change(date, in_type, out_type):
    return datetime.datetime.strptime(str(date), in_type).strftime(out_type)
