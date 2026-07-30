"""repro_09: deeply nested try/except inside try/except inside for-loop.

    Three-level nesting: outer try (BaseException) → for-loop → middle try (KeyError) → inner try (ZeroDivisionError).
"""
def f(items):
    ret = 0
    try:
        for x in items:
            try:
                v = int(x)
                try:
                    ret += 100 // v
                except ZeroDivisionError:
                    ret += 1
            except ValueError:
                ret += 10
        return ret
    except BaseException:
        return -1
