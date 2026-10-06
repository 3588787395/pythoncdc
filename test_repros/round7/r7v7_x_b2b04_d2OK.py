# Source Generated with Decompyle++ (Python version)
# File: r7v7_x_b2b04_d2.pyc (Python 3.11)

def x_b2b04_d2(xs, flag):
    acc = 0
    for x in xs:
        if flag:
            if x > 0:
                acc += x
                acc += 1
                continue
    return acc
