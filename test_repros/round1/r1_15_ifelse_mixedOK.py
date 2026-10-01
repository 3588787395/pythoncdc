# Source Generated with Decompyle++ (Python version)
# File: r1_15_ifelse_mixed.pyc (Python 3.11)

def f(a, b, c):
    total = 0
    if a and b or c:
        total += 4
    else:
        total -= 1
    return total
