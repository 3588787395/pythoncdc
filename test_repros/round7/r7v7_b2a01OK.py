# Source Generated with Decompyle++ (Python version)
# File: r7v7_b2a01.pyc (Python 3.11)

def b2a01_shallow(xs, flag):
    acc = 0
    for x in xs:
        if x > 3:
            continue
        acc += x
        continue
    return acc
def b2a01_deep(xs, flag):
    acc = 0
    for x in xs:
        if flag:
            if x > 1:
                if x > 2:
                    if x > 3:
                        continue
                    acc -= 1
                acc += 2
            acc += 3
        acc += x
    return acc
