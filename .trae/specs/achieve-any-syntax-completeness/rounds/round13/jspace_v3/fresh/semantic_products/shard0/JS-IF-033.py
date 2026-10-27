# Source Generated with Decompyle++ (Python version)
# File: r1_17_elif_mixed.pyc (Python 3.11)

def f(a, b, c, x):
    total = 0
    if x:
        total += 1
    elif a and b or c:
        total += 4
    return total
