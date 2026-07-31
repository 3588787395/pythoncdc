"""R14 DEFECT-REPRO 01: get_qry_date `curr` branch — nested if-in-else flattening.

Pattern (mirrors tools.pyc get_qry_date, date_type=='curr' else-branch):
    if date is None:
        ...
    elif isinstance(date, datetime.date):
        ...
    else:
        if len(date) == 8:            # sequential if (always evaluated)
            date = date_str_type_change(...)
        if date >= now:               # sequential if (always evaluated)
            ...
        else:
            ...

Decompiler tends to flatten the two sequential `if` statements inside the
`else` block into `elif` chains (mutually exclusive), which changes both
control-flow semantics and bytecode layout (jump targets / NOP markers).
This isolates the nested-if-in-else flattening mismatch pattern.
"""
import datetime


def get_qry_date_curr(now, date=None, date_type='pre'):
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
    return date


def date_str_type_change(date, in_type, out_type):
    return datetime.datetime.strptime(str(date), in_type).strftime(out_type)
