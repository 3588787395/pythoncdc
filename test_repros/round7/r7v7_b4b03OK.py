# Source Generated with Decompyle++ (Python version)
# File: r7v7_b4b03.pyc (Python 3.11)

def b4b03_shallow(xs, k):
    try:
        v = xs[0]
    except IndexError:
        v = -1
    else:
        v = v + k
    return v
def b4b03_deep(xs, k, flag):
    if flag and k > 0:
        try:
            v = xs[0]
        except IndexError:
            v = -1
        else:
            v = v + k
    return v
