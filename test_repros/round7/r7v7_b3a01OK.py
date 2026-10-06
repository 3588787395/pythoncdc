# Source Generated with Decompyle++ (Python version)
# File: r7v7_b3a01.pyc (Python 3.11)

def b3a01_shallow(xs, flag):
    acc = 0
    for x in xs:
        if x > 0:
            acc += x
        acc += 1
    return acc
def b3a01_deep(xs, flag):
    acc = 0
    for x in xs:
        if flag:
            if x > 0:
                if x > 10:
                    acc += 100
                else:
                    acc += x
            acc += 1
        acc += 2
    return acc
