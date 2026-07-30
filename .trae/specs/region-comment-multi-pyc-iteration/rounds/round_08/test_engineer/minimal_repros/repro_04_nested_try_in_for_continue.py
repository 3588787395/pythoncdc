"""repro_04: nested try/except inside for-loop with continue.

    def f(items):
        ret = 0
        try:
            for x in items:
                if x < 0:
                    continue
                try:
                    ret += 1 // x
                except ZeroDivisionError:
                    ret += 100
            return ret
        except BaseException:
            return -1
"""
def f(items):
    ret = 0
    try:
        for x in items:
            if x < 0:
                continue
            try:
                ret += 1 // x
            except ZeroDivisionError:
                ret += 100
        return ret
    except BaseException:
        return -1
