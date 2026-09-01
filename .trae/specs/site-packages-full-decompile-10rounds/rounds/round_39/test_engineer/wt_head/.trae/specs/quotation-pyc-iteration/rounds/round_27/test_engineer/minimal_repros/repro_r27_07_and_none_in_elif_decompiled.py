# Source Generated with Decompyle++ (Python version)
# File: repro_r27_07_and_none_in_elif.pyc (Python 3.11)

def f(a, b):
    if a is None:
        return 0
    elif a is not None and b is None:
        return 1
    return 2
