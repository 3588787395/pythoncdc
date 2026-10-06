# Source Generated with Decompyle++ (Python version)
# File: r3_b11_for_else_tail_join.pyc (Python 3.11)

def f(cond, syms, x):
    for s in syms:
        if cond:
            break
        use(s)
    else:
        x = mk(1)
    return x
