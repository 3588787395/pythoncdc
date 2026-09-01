"""R14 DEFECT-REPRO 03: nested-if-in-else flattening with string/method calls.

Isolation of the flattening pattern with function/method calls in branches
(mirrors get_qry_date's else-branch shape without isinstance). The
if/elif/else chain's else block contains two sequential `if` statements with
function calls; the decompiler flattens them into elif arms, renumbering
jump targets.

    if date is None:
        date = get_day(now)
    elif check(date):
        date = format_date(date)
    else:
        if len(date) == 8:
            date = change_type(date)
        if date >= now:
            date = get_day(now)
        else:
            date = get_day(date)
"""


def nested_if_in_else(date, now):
    if date is None:
        date = get_day(now)
    elif check(date):
        date = format_date(date)
    else:
        if len(date) == 8:
            date = change_type(date)
        if date >= now:
            date = get_day(now)
        else:
            date = get_day(date)
    return date
