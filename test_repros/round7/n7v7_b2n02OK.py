# Source Generated with Decompyle++ (Python version)
# File: n7v7_b2n02.pyc (Python 3.11)

def n2c(xs, flag):
    acc = 0
    for x in xs:
        if x < 0:
            acc -= 1
            continue
        acc += x
        continue
    acc += 1000
    return acc
def n2d(xs, k):
    n = 0
    for x in xs:
        if x == k:
            continue
        n += 1
        continue
    return n
