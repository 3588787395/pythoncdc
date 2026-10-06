# Source Generated with Decompyle++ (Python version)
# File: r5v5r_b115_nested_for_while.pyc (Python 3.11)

def f(xs):
    r = 0
    for i in xs:
        while i > 0:
            i -= 1
            r += i
    return r
