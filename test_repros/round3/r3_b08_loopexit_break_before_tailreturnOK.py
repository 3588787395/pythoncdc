# Source Generated with Decompyle++ (Python version)
# File: r3_b08_loopexit_break_before_tailreturn.pyc (Python 3.11)

def f(a, syms, x):
    res = None
    if a:
        res = mk(1)
    for s in syms:
        if s:
            res = mk(2)
            break
        use(s)
    return res
