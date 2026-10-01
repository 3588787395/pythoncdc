# Source Generated with Decompyle++ (Python version)
# File: rv_01_stmt_mixed_forinwhile.pyc (Python 3.11)

def f(a, b, c, x):
    total = 0
    while x:
        for i in range(3):
            if a and b or c:
                total += 1
        total += 2
    return total
