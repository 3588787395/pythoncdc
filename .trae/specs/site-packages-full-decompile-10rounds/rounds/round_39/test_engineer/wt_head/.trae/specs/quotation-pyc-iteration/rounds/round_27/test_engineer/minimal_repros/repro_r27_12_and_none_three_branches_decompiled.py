# Source Generated with Decompyle++ (Python version)
# File: repro_r27_12_and_none_three_branches.pyc (Python 3.11)

def f(a, b, c):
    if a is not None and b is None:
        return 1
    elif a is None and c is not None:
        return 2
    elif b is not None and c is None:
        return 3
    else:
        return 0
