"""repro_05: nested try/except inside for-loop with break.

    def f(items):
        ret = 0
        try:
            for x in items:
                if x < 0:
                    break
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
                break
            try:
                ret += 1 // x
            except ZeroDivisionError:
                ret += 100
        return ret
    except BaseException:
        return -1
