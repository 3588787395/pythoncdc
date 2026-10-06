# Source Generated with Decompyle++ (Python version)
# File: r7v7_b3b01.pyc (Python 3.11)

def b3b01_shallow(xs, flag):
    acc = 0
    for x in xs:
        if x < 0:
            continue
        acc += x
        continue
    return acc
def b3b01_deep(xs, flag):
    acc = 0
    for x in xs:
        if flag:
            if acc >= 0:
                if x < 0:
                    continue
                acc += x
            continue
        acc -= 1
    return acc
