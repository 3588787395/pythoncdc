# Source Generated with Decompyle++ (Python version)
# File: rv2_06_trywrap_r1_10_shape.pyc (Python 3.11)

def f(a, b, c):
    total = 0
    n = 0
    try:
        if a and b or c:
            total += 1
            n += 1
            if n > 9:
                pass
            else:
                if a:
                    pass
    except TypeError:
        total = -1
    return total
