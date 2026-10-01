# Source Generated with Decompyle++ (Python version)
# File: rv2_05_trywrap_r1_01_shape.pyc (Python 3.11)

def f(a, b, c):
    total = 0
    try:
        if a and b or c:
            total += 4
        total += 1
    except TypeError:
        total -= 1
    return total
