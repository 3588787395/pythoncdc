# Source Generated with Decompyle++ (Python version)
# File: r7v7_b4b01.pyc (Python 3.11)

def b4b01_shallow(xs, flag):
    acc = 0
    for x in xs:
        if x > 0:
            acc += 1
            continue
        acc -= 1
        continue
    return acc
def b4b01_deep(xs, flag):
    acc = 0
    if flag:
        for x in xs:
            if x > 0:
                if x > 10:
                    if x > 100:
                        acc += 3
                        continue
                    acc += 2
                    continue
                    continue
                acc += 1
                continue
            elif x < -10:
                acc -= 3
                continue
            else:
                acc -= 1
                continue
    return acc
