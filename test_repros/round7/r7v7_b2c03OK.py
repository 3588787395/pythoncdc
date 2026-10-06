# Source Generated with Decompyle++ (Python version)
# File: r7v7_b2c03.pyc (Python 3.11)

def b2c03_shallow(xs, k):
    acc = 0
    for x in xs:
        if x == k:
            continue
    return acc
def b2c03_deep(xs, k, flag):
    acc = 0
    while xs:
        if flag and acc >= 0:
            if xs[0] == k:
                continue
            else:
                break
        acc += 1
        xs = xs[1:]
    return acc
