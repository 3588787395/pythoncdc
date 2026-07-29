# Source Generated with Decompyle++ (Python version)
# File: repro_r29_06_elif_else_then_if.pyc (Python 3.11)

def f(x, y):
    if x == 1:
        y = 10
    elif x == 2:
        y = 20
    else:
        y = 30
    if y > 15:
        return 1
    else:
        return 0
