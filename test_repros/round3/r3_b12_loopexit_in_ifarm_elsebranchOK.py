# Source Generated with Decompyle++ (Python version)
# File: r3_b12_loopexit_in_ifarm_elsebranch.pyc (Python 3.11)

def f(cond, syms, x):
    if cond:
        for s in syms:
            if s:
                break
            use(s)
    else:
        x = mk(1)
    return x
