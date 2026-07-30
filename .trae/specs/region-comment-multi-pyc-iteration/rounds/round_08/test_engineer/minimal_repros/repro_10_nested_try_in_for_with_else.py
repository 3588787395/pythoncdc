"""repro_10: nested try/except inside for-loop with else clause on try.

    The inner try has an `else:` clause (runs when no exception).
"""
def f(items):
    ret = 0
    try:
        for x in items:
            try:
                v = int(x)
            except ValueError:
                ret += 1
            else:
                ret += v
        return ret
    except BaseException:
        return -1
