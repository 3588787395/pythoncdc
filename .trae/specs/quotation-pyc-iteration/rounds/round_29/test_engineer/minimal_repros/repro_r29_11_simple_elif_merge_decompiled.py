# Source Generated with Decompyle++ (Python version)
# File: repro_r29_11_simple_elif_merge.pyc (Python 3.11)

def f(x):
    if x == 1:
        x = 10
    elif x == 2:
        x = 20
    if x > 15:
        return 1
    else:
        return 0
