# Source Generated with Decompyle++ (Python version)
# File: r7v7_b2b02.pyc (Python 3.11)

def b2b02_shallow(xs, flag):
    for x in xs:
        if x is None:
            return False
    return True
def b2b02_deep(xs, flag):
    n = 0
    for x in xs:
        if flag and x > 0:
            if x is None:
                return False
            n += 1
    return n
