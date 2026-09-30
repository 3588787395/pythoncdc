# Source Generated with Decompyle++ (Python version)
# File: r1_17_elif_mixed.pyc (Python 3.11)

def f(a, b, c, x):
    total = 0
    if x:
        total += 1
    else:
        if not (a and b):
            total += 4
        if c:
            pass
        else:
            return total
