# Source Generated with Decompyle++ (Python version)
# File: repro_r29_12_complex_elif_merge.pyc (Python 3.11)

def f(x, y, z):
    if x == 1:
        y = 10
        return 0
    elif x == 2:
        y = 20
    elif x == 3:
        y = 30
    elif x == 4:
        if z:
            return z
        else:
            return y
    elif y is None:
        pass
    return y
