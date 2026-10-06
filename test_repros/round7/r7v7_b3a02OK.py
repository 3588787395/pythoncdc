# Source Generated with Decompyle++ (Python version)
# File: r7v7_b3a02.pyc (Python 3.11)

def b3a02_shallow(n, flag):
    s = 0
    while n > 0:
        if n % 2 == 0:
            s += n
        n -= 1
    return s
def b3a02_deep(n, flag):
    s = 0
    while n > 0:
        if flag:
            if n > 5:
                if n % 2 == 0:
                    s += n
                else:
                    s += 1
            n -= 1
        else:
            s += 2
            n -= 2
    return s
