# Source Generated with Decompyle++ (Python version)
# File: r1_04_nested_if_mixed.pyc (Python 3.11)

def f(a, b, c, x):
    total = 0
    if x:
        if not (a and b):
            total += 4
        if c:
            pass
        else:
            return total
