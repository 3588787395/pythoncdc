# Source Generated with Decompyle++ (Python version)
# File: r2_06_loop_try_continue.pyc (Python 3.11)

def f(items, key):
    out = []
    for it in items:
        try:
            out.append(it[key])
        except KeyError:
            out.append(None)
        out.append('tail')
    return out
def g(items, key):
    out = []
    for it in items:
        try:
            if it[key] < 0:
                continue
        except KeyError:
            continue
        out.append(it)
    return out
