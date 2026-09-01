"""repro_12 (CTRL): try/except NOT inside a loop — should NOT trigger T3.

    Control case: a plain try/except with no enclosing/enclosed loop.
    Used to verify the fix doesn't break the non-loop case.
"""
def f(items):
    ret = 0
    try:
        ret += len(items)
        return ret
    except BaseException:
        return -1
