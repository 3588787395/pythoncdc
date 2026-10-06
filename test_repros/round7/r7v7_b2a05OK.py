# Source Generated with Decompyle++ (Python version)
# File: r7v7_b2a05.pyc (Python 3.11)

def b2a05_shallow(xs, flag):
    acc = 0
    for x in xs:
        if x > 5:
            acc -= 1
            continue
        acc += x
        continue
    return acc
def b2a05_deep(xs, flag):
    acc = 0
    while xs:
        if flag and acc > 0:
            if len(xs) > 5:
                acc -= 1
                continue
            acc += 1
        xs = xs[1:]
    return acc
