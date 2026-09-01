"""R14 DEFECT-REPRO 06: nested-if-in-else with isinstance branch.

Variant of the nested-if-in-else pattern where the outer elif uses
`isinstance` (mirrors get_qry_date's `elif isinstance(date, datetime.date)`).
The isinstance branch + sequential ifs in else triggers the same flattening
tendency and jump-target renumbering.
"""
import datetime


def nested_isinstance(now, date=None):
    if date is None:
        day = now
        date = get_day(day)
    elif isinstance(date, datetime.date):
        date = date.strftime('%Y-%m-%d')
    else:
        if len(date) == 8:
            date = change_type(date, '%Y%m%d', '%Y-%m-%d')
        if date >= now:
            day = now
            date = get_day(day)
        else:
            day = date
            date = get_day(day)
    return date
