# Source Generated with Decompyle++ (Python version)
# File: n2_03_while_plain_try.pyc (Python 3.11)

def f(n, d):
    acc = 0
    while n > 0:
        try:
            acc += d[n]
        except KeyError:
            acc -= 1
        n -= 1
    return acc
