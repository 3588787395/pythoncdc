# Source Generated with Decompyle++ (Python version)
# File: r4v3_a11_try_if_tail_b100.pyc (Python 3.11)

def f(d):
    try:
        if d.kind == 1:
            out = build(d.a)
        elif d.kind == 2:
            out = build(d.b)
        else:
            out = None
        return out
    except Exception:
        LOG.error('x')
        return None
