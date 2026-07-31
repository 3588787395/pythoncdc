"""R14 DEFECT-REPRO 07: nested-if-in-else with function-call branches.

Variant where the sequential ifs inside else call functions with keyword
arguments (mirrors get_qry_date's `get_trade_days(end_date=day, count=1)[0]`
pattern). The KW_NAMES + PRECALL + CALL instruction sequence inside the
nested-if-in-else amplifies the offset-shift / NOP-marker mismatch when the
decompiler renumbers jump targets.
"""


def nested_call_branch(date_type, now, date=None):
    if date_type == 'curr':
        if date is None:
            day = now
            date = get_trade_days(end_date=day, count=1)[0]
        else:
            if len(date) == 8:
                date = change_type(date)
            if date >= now:
                day = now
                date = get_trade_days(end_date=day, count=1)[0]
            else:
                day = date
                date = get_trade_days(end_date=day, count=1)[0]
        return date
    return date
