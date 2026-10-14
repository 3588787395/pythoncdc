# Source Generated with Decompyle++ (Python version)
# File: r2v3_b20_except_continue_after_pop_except.pyc (Python 3.11)

def f(items, w):
    for x in items:
        try:
            v = w(x)
        except ValueError:
            continue
        w(v)
