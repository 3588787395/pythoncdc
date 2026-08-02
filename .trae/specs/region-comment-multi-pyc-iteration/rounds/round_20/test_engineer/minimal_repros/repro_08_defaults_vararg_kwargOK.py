# Source Generated with Decompyle++ (Python version)
# File: repro_08_defaults_vararg_kwarg.pyc (Python 3.11)

def f(a=1, *args, sep=' ', **kwargs):
    return (a, args, sep, kwargs)
result = f(2, 3, sep='-', mode='x')
