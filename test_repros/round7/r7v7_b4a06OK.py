# Source Generated with Decompyle++ (Python version)
# File: r7v7_b4a06.pyc (Python 3.11)

def b4a06_shallow(a, b):
    try:
        a + b
    finally:
        a = b
    return a
def b4a06_deep(a, b, flag):
    if flag and a > 0:
        try:
            a + b
        finally:
            a = b
    return a
