# Source Generated with Decompyle++ (Python version)
# File: repro_05_vararg_kwarg.pyc (Python 3.11)

def f(*args, **kwargs):
    return (args, kwargs)
result = f(1, 2, x=3)
