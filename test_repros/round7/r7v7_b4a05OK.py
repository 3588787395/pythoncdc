# Source Generated with Decompyle++ (Python version)
# File: r7v7_b4a05.pyc (Python 3.11)

def b4a05_shallow(path, xs, flag):
    acc = 0
    with open(path) as f:
        for x in xs:
            if x > 0:
                acc += x
            acc += 1
    return acc
def b4a05_deep(path, xs, flag):
    acc = 0
    with open(path) as f:
        if flag:
            for x in xs:
                if x > 0:
                    if x > 10:
                        acc += 10
                    else:
                        acc += x
                acc += 1
    return acc
