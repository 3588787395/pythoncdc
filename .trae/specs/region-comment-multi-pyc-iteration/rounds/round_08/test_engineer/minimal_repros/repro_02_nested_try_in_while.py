"""repro_02: nested try/except inside while-loop.

    def f(items):
        ret = 0
        i = 0
        try:
            while i < len(items):
                try:
                    ret += items[i]
                except IndexError:
                    ret += 1
                i += 1
            return ret
        except BaseException:
            return -1
"""
def f(items):
    ret = 0
    i = 0
    try:
        while i < len(items):
            try:
                ret += items[i]
            except IndexError:
                ret += 1
            i += 1
        return ret
    except BaseException:
        return -1
