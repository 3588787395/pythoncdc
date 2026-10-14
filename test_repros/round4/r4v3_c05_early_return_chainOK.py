# Source Generated with Decompyle++ (Python version)
# File: r4v3_c05_early_return_chain.pyc (Python 3.11)

def f(d, kind):
    if kind == 1:
        return d
    elif kind == 2:
        d = prep(d)
    else:
        return d
    return d
