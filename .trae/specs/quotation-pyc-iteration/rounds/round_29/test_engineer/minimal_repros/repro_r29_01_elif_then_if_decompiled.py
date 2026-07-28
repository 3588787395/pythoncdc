# Source Generated with Decompyle++ (Python version)
# File: repro_r29_01_elif_then_if.pyc (Python 3.11)

def f(x, y):
    if x == 1:
        y = 10
    elif x == 2:
        y = 20
    elif x == 3:
        y = 30
    if y is None:
        return 0
    else:
        return y
