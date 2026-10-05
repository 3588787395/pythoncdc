# Source Generated with Decompyle++ (Python version)
# File: e12c_g9_yield_arg.pyc (Python 3.11)

def f_yield_expr_arg(xs):
    def sink(x):
        return x
    for i in range(3):
        if i:
            yield sink(yield i)
