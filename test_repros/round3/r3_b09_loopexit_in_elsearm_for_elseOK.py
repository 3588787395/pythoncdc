# Source Generated with Decompyle++ (Python version)
# File: r3_b09_loopexit_in_elsearm_for_else.pyc (Python 3.11)

def f(a, syms, x):
    if a:
        res = mk(1)
    else:
        for s in syms:
            use(s)
            if s > 1:
                break
        else:
            res = mk(x)
        return res
