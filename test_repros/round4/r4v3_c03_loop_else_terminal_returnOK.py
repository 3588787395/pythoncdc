# Source Generated with Decompyle++ (Python version)
# File: r4v3_c03_loop_else_terminal_return.pyc (Python 3.11)

def f(symbols, mk):
    res = mk(0)
    for s in symbols:
        if s:
            res = mk(s)
            break
    else:
        res = mk(-1)
    return res
