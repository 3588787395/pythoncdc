# Source Generated with Decompyle++ (Python version)
# File: r7v7_b2b01.pyc (Python 3.11)

def b2b01_shallow(xs, flag):
    acc = 0
    for x in xs:
        if x > 9:
            break
        acc += x
    return acc
def b2b01_deep(xs, flag):
    acc = 0
    for x in xs:
        if flag and acc > 0:
            if x > 9:
                break
            acc += 1
        acc += x
    return acc
