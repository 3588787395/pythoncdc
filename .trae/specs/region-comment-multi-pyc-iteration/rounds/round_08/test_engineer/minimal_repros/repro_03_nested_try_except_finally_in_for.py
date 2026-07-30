"""repro_03: nested try/except/finally inside for-loop.

    def f(items):
        ret = 0
        try:
            for x in items:
                try:
                    ret += int(x)
                except ValueError:
                    ret += 1
                finally:
                    ret += 0
            return ret
        except BaseException:
            return -1
"""
def f(items):
    ret = 0
    try:
        for x in items:
            try:
                ret += int(x)
            except ValueError:
                ret += 1
            finally:
                ret += 0
        return ret
    except BaseException:
        return -1
