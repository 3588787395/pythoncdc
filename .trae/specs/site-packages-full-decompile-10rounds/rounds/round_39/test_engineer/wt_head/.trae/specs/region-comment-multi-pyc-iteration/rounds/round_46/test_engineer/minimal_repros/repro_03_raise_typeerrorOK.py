# Source Generated with Decompyle++ (Python version)
# File: repro_03_raise_typeerror.pyc (Python 3.11)

def func(x):
    if not isinstance(x, int):
        raise TypeError('not int')
    return x
