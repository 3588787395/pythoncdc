"""repro_08: nested try/except inside for-loop with assignment in except.

    Mirrors graph.pyc create_full_graph closely: outer try wraps a for-loop,
    inner try/except KeyError inside loop, assignment in except handler.
"""
def f(items):
    result = {}
    try:
        for x in items:
            key = x[0]
            try:
                result[key].append(x)
            except KeyError:
                result[key] = [x]
        return len(result)
    except BaseException:
        return -1
