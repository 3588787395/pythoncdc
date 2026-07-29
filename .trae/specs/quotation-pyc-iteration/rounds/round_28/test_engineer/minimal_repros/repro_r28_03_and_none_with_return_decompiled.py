# Source Generated with Decompyle++ (Python version)
# File: repro_r28_03_and_none_with_return.pyc (Python 3.11)

def f(a, b):
    if a is not None and b is None:
        return 1
    elif a is None and b is not None:
        return 2
    return 0
