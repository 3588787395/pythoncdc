# Source Generated with Decompyle++ (Python version)
# File: r7v7_b4a01.pyc (Python 3.11)

def b4a01_shallow(xs, flag):
    acc = 0
    for x in xs:
        if x > 0:
            if x > 5:
                acc += 5
            else:
                acc += x
        acc += 1
    return acc
def b4a01_deep(xs, flag):
    acc = 0
    for x in xs:
        if x != 0:
            if x > 0:
                if x > 5:
                    if x > 50:
                        acc += 50
                    else:
                        acc += 5
                else:
                    acc += x
            acc += 1
        acc += 2
    return acc
