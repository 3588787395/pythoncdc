# Source Generated with Decompyle++ (Python version)
# File: repro_r29_08_deep_elif_chain.pyc (Python 3.11)

def f(x, y, z):
    if x == 1:
        if y == 1:
            z = 10
        elif y == 2:
            z = 20
        if z is None:
            return 0
        else:
            return z
    elif x == 2:
        z = 30
