# Source Generated with Decompyle++ (Python version)
# File: r7v7_b4c01.pyc (Python 3.11)

def b4c01_shallow(xs, flag):
    acc = 0
    for x in xs:
        if x > 0:
            if flag:
                acc += x
            else:
                acc -= x
        acc += 1
    return acc
def b4c01_deep(xs, flag):
    acc = 0
    for x in xs:
        if x != 0 and x > 0:
            if flag:
                if x > 100:
                    acc += 100
                else:
                    acc += x
            else:
                acc -= x
        acc += 1
    return acc
