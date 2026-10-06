# Source Generated with Decompyle++ (Python version)
# File: r4v3_c04_loop_plain_control.pyc (Python 3.11)

def f(symbols, mk):
    res = mk(0)
    for s in symbols:
        if s:
            res = mk(s)
    return res
