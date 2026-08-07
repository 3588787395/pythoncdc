# Source Generated with Decompyle++ (Python version)
# File: repro_04_nested_raise.pyc (Python 3.11)

def func(x):
    if x < 0:
        raise ValueError('negative')
    elif x > 100:
        raise OverflowError('too large')
    return x
