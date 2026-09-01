"""R13 repro_01: while loop inside if/elif/else else-branch.

Region type: LoopRegion + IfRegion (if/elif/else chain)
Violated principle: 2 (unique ownership) + 3 (nesting as abstract node)
Corresponding function: get_date_and_count (candle_period==8)

Defect: The while loop's backward walk absorbs the if/elif/else condition
blocks into the LoopRegion because the elif condition's False branch jumps
to the while loop's condition_block. This causes the IfRegion to have
parent=LoopRegion (if/elif chain inside loop), losing the if/elif chain.

Source pattern:
    if cond_a:
        ...
    elif cond_b:
        ...
    else:
        count -= 1
        while count > 0:
            if sub_cond:
                ...
            else:
                ...
        if post_cond:
            result = expr_a
        else:
            result = expr_b
"""
from datetime import datetime, timedelta


def get_date_and_count_repro(query_date, count, candle_period):
    query_date = datetime.strptime(query_date, '%Y%m%d')
    if candle_period == 7:
        a = query_date.isocalendar()
        start_date = datetime.strftime(query_date - timedelta(a[2] - 1), '%Y%m%d')
    elif candle_period == 8:
        year = query_date.year
        month = query_date.month
        query_date = datetime.strftime(query_date, '%Y%m%d')
        this_month_start_date = query_date[:6] + '01'
        if len([this_month_start_date]) == 0:
            query_date = datetime.strftime(query_date, '%Y%m%d')
            while count > 0:
                if month - count <= 0:
                    year -= 1
                    count -= month
                    month = 12
                else:
                    month = month - count
                    count = 0
            if month in (10, 11, 12):
                start_date = str(year) + str(month) + '01'
            else:
                start_date = str(year) + '0' + str(month) + '01'
        elif count == 1 and count > 0:
            if month - count <= 0:
                year -= 1
                count -= month
                month = 12
            else:
                month = month - count
                count = 0
        count -= 1
        while count > 0:
            if month - count <= 0:
                year -= 1
                count -= month
                month = 12
            else:
                month = month - count
                count = 0
        if month in (10, 11, 12):
            start_date = str(year) + str(month) + '01'
        else:
            start_date = str(year) + '0' + str(month) + '01'
    return (start_date, query_date)
