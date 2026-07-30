"""repro_07: nested try/except inside for-loop with return in try body.

    def f(items):
        try:
            for x in items:
                try:
                    if x == 0:
                        return 0
                    v = 1 // x
                except ZeroDivisionError:
                    v = -1
            return v
        except BaseException:
            return -2
"""
def f(items):
    try:
        for x in items:
            try:
                if x == 0:
                    return 0
                v = 1 // x
            except ZeroDivisionError:
                v = -1
        return v
    except BaseException:
        return -2
