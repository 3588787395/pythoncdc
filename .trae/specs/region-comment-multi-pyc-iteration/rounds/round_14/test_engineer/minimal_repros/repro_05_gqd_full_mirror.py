"""R14 DEFECT-REPRO 05: full get_qry_date mirror with import-inside-function.

Full mirror of tools.pyc get_qry_date: `from ... import` inside the function
body, if/elif over date_type, nested if/elif/else with sequential ifs in the
else branch, and per-branch `return date`. Combines all get_qry_date
sub-patterns (import + if/elif + nested-if-in-else + return) into one repro
to isolate the cumulative NOP / jump-target renumbering mismatch.
"""
import datetime


def get_qry_date(now, date=None, date_type='pre'):
    from fly.common.tradingday_calendar import get_trade_days, is_trading_day
    if date_type == 'curr':
        if date is None:
            day = now
            date = get_trade_days(end_date=day, count=1)[0]
        elif isinstance(date, datetime.date):
            date = date.strftime('%Y-%m-%d')
        else:
            if len(date) == 8:
                date = date_str_type_change(date, '%Y%m%d', '%Y-%m-%d')
            if date >= now:
                day = now
                date = get_trade_days(end_date=day, count=1)[0]
            else:
                day = date
                date = get_trade_days(end_date=day, count=1)[0]
        return date
    elif date_type == 'pre':
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
