# Source Generated with Decompyle++ (Python version)
# File: r2_15_reraise.pyc (Python 3.11)

def f(x):
    try:
        try:
            if x < 0:
                raise ValueError('neg')
            x += 1
        except ValueError:
            if x == -1:
                raise
            x = -x
    except ValueError as e:
        return -100
    return x
