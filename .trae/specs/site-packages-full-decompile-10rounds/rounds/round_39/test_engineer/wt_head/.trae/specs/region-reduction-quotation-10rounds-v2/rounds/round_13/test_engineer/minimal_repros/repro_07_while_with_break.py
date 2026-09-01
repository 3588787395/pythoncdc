"""R13 repro_07: while loop with break inside if/elif chain.

Region type: LoopRegion (with break) + IfRegion
Violated principle: N/A (control case — break distinguishes while-else
from regular fall-through)
Corresponding function: get_date_and_count (control)

Defect: When breaks ARE present, _find_loop_else correctly identifies
the else clause (skipped by break). This repro verifies the positive
case to ensure no regression when fixing the no-break case.
"""
def func(x, n):
    if x == 1:
        result = 1
    else:
        while n > 0:
            if n == 5:
                break
            n -= 1
        else:
            result = 'completed'
            return result
        result = 'broken'
    return result
