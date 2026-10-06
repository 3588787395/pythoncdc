# Source Generated with Decompyle++ (Python version)
# File: r5v5r_b115_for_if_while.pyc (Python 3.11)

def f(xs):
    r = 0
    for i in xs:
        if i:
            while i > 0:
                r = i
                i -= 1
    return r
