# Source Generated with Decompyle++ (Python version)
# File: b6576_probe.pyc (Python 3.11)

def chain3_boolop(x, y):
    a = b = c = x > 0 and y > 0
    return a + b + c
def chain2_boolop(x, y):
    a = b = x > 0 and y > 0
    return a + b
def aug_boolop(x, a, b):
    x += a and b
    return x
