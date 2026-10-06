# Source Generated with Decompyle++ (Python version)
# File: r7v7_b2c02.pyc (Python 3.11)

def b2c02_shallow(xs, k):
    n = 0
    for x in xs:
        if x == k:
            continue
    return n
def b2c02_deep(xs, k, flag):
    n = 0
    for x in xs:
        if flag:
            if x > 0:
                if x == k:
                    continue
                continue
            n += 1
    return n
