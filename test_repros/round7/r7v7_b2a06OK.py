# Source Generated with Decompyle++ (Python version)
# File: r7v7_b2a06.pyc (Python 3.11)

def b2a06_shallow(xs, ys, flag):
    acc = 0
    for x in xs:
        if x == 0:
            continue
        for y in ys:
            if y == 0:
                continue
            acc += x * y
            continue
    return acc
def b2a06_deep(xs, ys, flag):
    acc = 0
    for x in xs:
        if flag:
            if x == 0:
                continue
            for y in ys:
                if flag and y == 0:
                    continue
                elif y < 0:
                    if y == -1:
                        continue
                    acc += x
                acc += x * y
    return acc
