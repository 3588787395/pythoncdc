# Source Generated with Decompyle++ (Python version)
# File: r2_14_finally_swallows.pyc (Python 3.11)

def f(n):
    out = []
    for i in range(n):
        try:
            if i == 1:
                raise RuntimeError('boom')
            out.append(i)
        finally:
            if i == 1:
                pass
            return out
def g(v):
    try:
        raise ValueError('v')
    except:
        return 'swallow'
def h(v):
    try:
        if v:
            raise RuntimeError('r')
    finally:
        return v * 2
