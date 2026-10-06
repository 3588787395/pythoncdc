# Source Generated with Decompyle++ (Python version)
# File: r7v7_b3b02.pyc (Python 3.11)

def b3b02_shallow(xs, k):
    for x in xs:
        if x == k:
            break
    else:
        return -1
    return 1
def b3b02_deep(xs, k, flag):
    res = 0
    if flag:
        for x in xs:
            if x > 0 and x == k:
                break
        else:
            res = -1
        res += 1
    return res
