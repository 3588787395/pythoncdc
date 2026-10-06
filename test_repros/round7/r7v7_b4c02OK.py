# Source Generated with Decompyle++ (Python version)
# File: r7v7_b4c02.pyc (Python 3.11)

def b4c02_shallow(xs, k):
    acc = 0
    for x in xs:
        try:
            if x == k:
                continue
            acc += x
        finally:
            acc += 1
    return acc
def b4c02_deep(xs, k, flag):
    acc = 0
    while xs:
        if flag:
            try:
                if xs[0] == k:
                    continue
                elif xs[0] > 0:
                    acc += xs[0]
            finally:
                acc += 1
        xs = xs[1:]
    return acc
