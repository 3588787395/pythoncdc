# Source Generated with Decompyle++ (Python version)
# File: rec1_yf9_arg.pyc (Python 3.11)

def f_yield_arg(xs):
    def sink(x):
        return x
    for i in range(3):
        if i:
            yield sink(yield i)
