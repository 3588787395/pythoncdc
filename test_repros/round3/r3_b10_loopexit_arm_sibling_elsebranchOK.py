# Source Generated with Decompyle++ (Python version)
# File: r3_b10_loopexit_arm_sibling_elsebranch.pyc (Python 3.11)

def f(cond, syms, x):
    if cond:
        for s in syms:
            use(s)
    else:
        x = mk(1)
    return x
