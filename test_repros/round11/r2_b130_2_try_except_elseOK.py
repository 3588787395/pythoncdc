# Source Generated with Decompyle++ (Python version)
# File: r2_b130_2_try_except_else.pyc (Python 3.11)

def g(x):
    try:
        y = int(x)
    except ValueError:
        y = 0
    else:
        y = y + 1
    print(y)
    return y
