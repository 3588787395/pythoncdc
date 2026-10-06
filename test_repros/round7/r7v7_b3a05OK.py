# Source Generated with Decompyle++ (Python version)
# File: r7v7_b3a05.pyc (Python 3.11)

def b3a05_shallow(xs, ys, flag):
    acc = 0
    for x in xs:
        if x > 0:
            for y in ys:
                if y > 0:
                    acc += x * y
                acc += y
        acc += x
    return acc
def b3a05_deep(xs, ys, flag):
    acc = 0
    for x in xs:
        if flag and x != 0:
            for y in ys:
                if flag and y != 0:
                    if y > 0:
                        acc += x * y
                    acc += y
            acc += x
        acc += 1
    return acc
