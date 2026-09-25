# Source Generated with Decompyle++ (Python version)
# File: r68b4_apib_inc2.pyc (Python 3.11)

def r68b4_apib_inc2(x, include, min_count):
    if x > 0:
        y = x
        if not include:
            min_count -= 1
    else:
        y = -x
    return (y, min_count)
