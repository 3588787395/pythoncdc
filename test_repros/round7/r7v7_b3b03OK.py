# Source Generated with Decompyle++ (Python version)
# File: r7v7_b3b03.pyc (Python 3.11)

def b3b03_shallow(n, k):
    while n > 0:
        if n == k:
            break
        n -= 1
    else:
        return -1
    return 1
def b3b03_deep(n, k, flag):
    res = 0
    while n > 0:
        if flag and n > 5 and n == k:
            break
        n -= 1
    else:
        res = -1
    return res
