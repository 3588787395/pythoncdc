# Source Generated with Decompyle++ (Python version)
# File: n7v7_b4n01.pyc (Python 3.11)

def n4a(x, flag):
    acc = 0
    try:
        if x > 0:
            acc += 1
        else:
            acc -= 1
    finally:
        acc += 10
    return acc
def n4b(xs, flag):
    acc = 0
    for x in xs:
        if x:
            acc += 1
    acc += 100
    return acc
