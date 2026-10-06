# Source Generated with Decompyle++ (Python version)
# File: r7v7_b3c02.pyc (Python 3.11)

def b3c02_shallow(xs, k):
    acc = 0
    for x in xs:
        if x == k:
            continue
        acc += x
        continue
    acc += 1000
    return acc
def b3c02_deep(xs, k, flag):
    acc = 0
    for x in xs:
        if flag:
            if x > 0 and x == k:
                continue
            acc += x
            continue
        acc -= 1
    acc += 1000
    return acc
