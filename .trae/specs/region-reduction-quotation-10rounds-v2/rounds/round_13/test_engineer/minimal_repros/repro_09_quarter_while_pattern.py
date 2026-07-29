"""R13 repro_09: while loop in else-branch with post-loop if/elif.

Region type: IfRegion (if/elif/else) + LoopRegion + IfRegion (post-loop)
Violated principle: 2 (unique ownership) + 3 (nesting as abstract node)
Corresponding function: get_date_and_count (candle_period==15)

Defect: Same pattern as candle_period==8 but with quarter calculation.
The while loop's backward walk absorbs the if/elif chain condition blocks,
and the post-loop if/else becomes a sibling.
"""
def func(candle_period, count, month, year):
    if candle_period == 15:
        if month // 3 == 0:
            end_date = str(year - 1) + '1231'
        elif month // 3 == 1:
            end_date = str(year) + '0331'
        elif month // 3 == 2:
            end_date = str(year) + '0630'
        elif month // 3 == 3:
            end_date = str(year) + '0930'
        if len([end_date]) == 0:
            pass
        elif count == 1 and count > 0:
            if month // 3 - count < 0:
                year -= 1
                count -= month // 3
                month = 13
            else:
                month = month - count * 3
                count = 0
        count -= 1
        while count > 0:
            if month // 3 - count < 0:
                year -= 1
                count -= month // 3
                month = 13
            else:
                month = month - count * 3
                count = 0
        if month in (10, 11, 12):
            start_date = str(year) + str(month) + '01'
        else:
            start_date = str(year) + '0' + str(month) + '01'
    return start_date
