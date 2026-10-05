# Source Generated with Decompyle++ (Python version)
# File: e12f_g9_yield_boolop.pyc (Python 3.11)

def f_yield_in_boolop(xs):
    for i in range(3):
        if i:
            yield yield i or 0
