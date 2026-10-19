# Source Generated with Decompyle++ (Python version)
# File: rec1_yf9_prec.pyc (Python 3.11)

def f_yield_binop(xs):
    for i in range(3):
        if i:
            v = (yield i) + 1
            yield v
