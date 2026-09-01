"""R14 DEFECT-REPRO 04: nested-if-in-else with inner if/else + function calls.

Variant where the if/elif/else chain's else block contains sequential ifs,
the second of which has an inner if/else (mirrors get_qry_date pre-branch
shape). The deeper nesting amplifies the flattening + jump-target renumbering.

    if date is None:
        date = get_day(now)
    elif check(date):
        date = format_date(date)
    else:
        if len(date) == 8:
            date = change_type(date)
        if date >= now:
            if is_valid(now):
                date = get_day(now)
            else:
                date = get_day2(now)
        else:
            date = get_day(date)
"""


def nested_if_inner(date, now):
    if date is None:
        date = get_day(now)
    elif check(date):
        date = format_date(date)
    else:
        if len(date) == 8:
            date = change_type(date)
        if date >= now:
            if is_valid(now):
                date = get_day(now)
            else:
                date = get_day2(now)
        else:
            date = get_day(date)
    return date
