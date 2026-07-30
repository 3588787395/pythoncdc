"""Repro 01 - build_future_fill_time core defect: if/else with for-loop INSIDE else block.

Original source structure (correct): the for-loop is the trailing statement of the
else block, shared by the nested if/elif/else sub-branches. The if-branch (typet!=5)
jumps PAST the for-loop to `if total`.

Defect: decompiler hoists the for-loop to top level (reached by ALL branches).
"""
def f(typet, suffix):
    trade_days = [1, 2, 3]
    total = []
    market = []
    if not typet == 5:
        if typet == 1:
            for today in trade_days:
                total.append(today)
    else:
        if suffix == 'A':
            market = [1]
        elif suffix in ('B', 'C'):
            market = [2]
        else:
            market = [3]
        for today in trade_days:
            for item in market:
                total.append(today + item)
    if total:
        total.sort()
    return total
