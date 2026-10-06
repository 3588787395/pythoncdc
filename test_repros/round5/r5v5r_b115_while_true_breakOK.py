# Source Generated with Decompyle++ (Python version)
# File: r5v5r_b115_while_true_break.pyc (Python 3.11)

def f(a):
    while a and a > 0:
        a -= 1
        if a < 0:
            break
    return a
