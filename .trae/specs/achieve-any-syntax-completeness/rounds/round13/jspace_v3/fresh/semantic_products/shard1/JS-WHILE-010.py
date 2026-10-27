# Source Generated with Decompyle++ (Python version)
# File: r1_10_while_mixed.pyc (Python 3.11)

def f(a, b, c):
    total = 0
    n = 0
    while a and b or c:
        total += 1
        n += 1
        if n > 9:
            break
    return total
