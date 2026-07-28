# Source Generated with Decompyle++ (Python version)
# File: repro_r28_08_and_none_elif_only.pyc (Python 3.11)

def f(a, b):
    if a:
        return 0
    elif a is not None and b is None:
        return 1
    return 2
