# Source Generated with Decompyle++ (Python version)
# File: rec1_yf9_ret.pyc (Python 3.11)

def f_yield_ret(xs):
    for i in range(3):
        if i:
            return (yield i)
    return 0
