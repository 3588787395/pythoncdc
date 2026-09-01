"""repro_01: nested try/except inside for-loop (minimal).

Source pattern (from graph.pyc create_full_graph):
    def f(items):
        ret = 0
        try:                          # OUTER try
            for x in items:
                try:                    # INNER try
                    ret += x['k']
                except KeyError:
                    ret += 1
            return ret
        except BaseException:          # OUTER except
            return -1
"""
def f(items):
    ret = 0
    try:
        for x in items:
            try:
                ret += x['k']
            except KeyError:
                ret += 1
        return ret
    except BaseException:
        return -1
