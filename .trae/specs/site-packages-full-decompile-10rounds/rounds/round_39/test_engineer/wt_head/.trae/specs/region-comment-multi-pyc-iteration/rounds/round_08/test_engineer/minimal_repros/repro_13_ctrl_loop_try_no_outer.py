"""repro_13 (CTRL): for-loop with try/except but NO outer try — no T3 trigger.

    Control case: only one level of try (inside the loop), no outer wrapping try.
    Should pass both before and after the fix.
"""
def f(items):
    ret = 0
    for x in items:
        try:
            ret += 1 // x
        except ZeroDivisionError:
            ret += 100
    return ret
