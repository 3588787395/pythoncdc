# Source Generated with Decompyle++ (Python version)
# File: repro_02_raise_in_except.pyc (Python 3.11)

def func(x):
    try:
        return x + 1
        return None
    except ValueError:
        raise ValueError('re-raise')
