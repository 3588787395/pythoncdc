# Source Generated with Decompyle++ (Python version)
# File: r7v7_b3c01.pyc (Python 3.11)

def b3c01_shallow(xs, flag):
    acc = 0
    for x in xs:
        if x == -1:
            continue
        elif x > 0:
            acc += x
        acc += 1
    return acc
def b3c01_deep(xs, flag):
    acc = 0
    for x in xs:
        if flag:
            if x == -1:
                continue
            if x > 0:
                if x > 100:
                    acc += 100
                else:
                    acc += x
            acc += 1
            continue
        acc += 2
    return acc
