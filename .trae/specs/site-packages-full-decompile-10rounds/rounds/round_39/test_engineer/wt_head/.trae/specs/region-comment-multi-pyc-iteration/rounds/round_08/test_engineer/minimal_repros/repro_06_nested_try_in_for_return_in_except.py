"""repro_06: nested try/except inside for-loop with return in except.

    def f(items):
        try:
            for x in items:
                try:
                    v = x['k']
                except KeyError:
                    return -1
            return len(items)
        except BaseException:
            return -2
"""
def f(items):
    try:
        for x in items:
            try:
                v = x['k']
            except KeyError:
                return -1
        return len(items)
    except BaseException:
        return -2
