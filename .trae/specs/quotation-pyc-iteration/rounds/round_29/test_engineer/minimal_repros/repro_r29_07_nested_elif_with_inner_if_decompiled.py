# Source Generated with Decompyle++ (Python version)
# File: repro_r29_07_nested_elif_with_inner_if.pyc (Python 3.11)

def f(a, b, c):
    if a:
        if b == 0:
            c = 1
            return 0
        elif b == 1:
            if c > 0:
                return 1
            else:
                return 2
        elif c is None:
            pass
    return c
