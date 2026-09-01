# Source Generated with Decompyle++ (Python version)
# File: repro_r27_06_and_mixed_none_checks.pyc (Python 3.11)

def f(a, b, c):
    if a is not None and b is None and c is not None:
        return 1
    else:
        return 0
