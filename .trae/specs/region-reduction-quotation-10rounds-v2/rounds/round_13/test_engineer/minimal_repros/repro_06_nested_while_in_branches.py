"""R13 repro_06: nested while loops in different if/elif branches.

Region type: IfRegion + 2x LoopRegion
Violated principle: 2 (unique ownership) + 3 (nesting as abstract node)
Corresponding function: get_date_and_count (candle_period==8 and ==15)

Defect: Two while loops in different branches of an if/elif/else chain.
The second while loop's backward walk may absorb the first branch's
condition blocks.
"""
def func(mode, a, b):
    if mode == 1:
        while a > 0:
            if a > 10:
                a -= 5
            else:
                a -= 1
        result = a
    elif mode == 2:
        b -= 1
        while b > 0:
            if b > 10:
                b -= 5
            else:
                b -= 1
        if b in (0, 1):
            result = 'low'
        else:
            result = 'high'
    else:
        result = -1
    return result
