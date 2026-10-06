# Source Generated with Decompyle++ (Python version)
# File: r7v7_b2b04.pyc (Python 3.11)

def b2b04_shallow(xs, flag):
    acc = 0
    for x in xs:
        if x > 0:
            acc += x
            acc += 1
            continue
    return acc
def b2b04_deep(xs, flag):
    acc = 0
    for x in xs:
        if flag:
            if x > 0:
                if x > 100:
                    acc -= x
                else:
                    acc += x
        else:
            acc += 2
        acc += 1
    return acc
