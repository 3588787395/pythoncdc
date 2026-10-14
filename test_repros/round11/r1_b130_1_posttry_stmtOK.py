# Source Generated with Decompyle++ (Python version)
# File: r1_b130_1_posttry_stmt.pyc (Python 3.11)

def f(x):
    try:
        y = int(x)
    except ValueError:
        y = 0
    print(y)
    return y
