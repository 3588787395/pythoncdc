# Source Generated with Decompyle++ (Python version)
# File: r7v7_b2c01.pyc (Python 3.11)

def b2c01_shallow(xs, flag):
    acc = 0
    for x in xs:
        if x % 2 == 0 and flag:
            continue
        acc += x
        acc += 1
        continue
    return acc
def b2c01_deep(xs, flag):
    acc = 0
    for x in xs:
        if flag and x > 0:
            if x % 2 == 0 and flag:
                continue
            acc += x
        acc += 1
        acc += acc > 1000
    return acc
