# Source Generated with Decompyle++ (Python version)
# File: r7v7_x_b4c03_d2.pyc (Python 3.11)

def x_b4c03_d2(xs, k):
    acc = 0
    for x in xs:
        if x > 0:
            if x == k:
                acc = -1
                break
            elif x > 10:
                acc += 10
                continue
            else:
                acc += x
                continue
        acc -= 1
    else:
        acc += 100
    return acc
