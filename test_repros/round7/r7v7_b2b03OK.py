# Source Generated with Decompyle++ (Python version)
# File: r7v7_b2b03.pyc (Python 3.11)

def b2b03_shallow(ks, flag):
    n = 0
    for k in ks:
        if k != 'x':
            if k == 'y':
                continue
            n += 1
    return n
def b2b03_deep(ks, flag):
    n = 0
    for k in ks:
        if flag and k != 'x':
            if k == 'y':
                continue
            n += 1
    return n
