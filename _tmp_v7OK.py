# Source Generated with Decompyle++ (Python version)
# File: _tmp_v7.pyc (Python 3.11)

def f(x, y, z, d):
    try:
        if x is None:
            return z
        elif x == 0:
            return z + 1
    except BaseException:
        return d
    return y
