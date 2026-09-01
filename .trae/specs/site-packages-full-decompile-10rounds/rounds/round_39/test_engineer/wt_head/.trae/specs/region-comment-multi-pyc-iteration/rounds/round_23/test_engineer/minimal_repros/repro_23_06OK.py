# Source Generated with Decompyle++ (Python version)
# File: repro_23_06.cpython-311.pyc (Python 3.11)

def boolop_in_if(a, b, c):
    if a > 0 and b > 0:
        return c
    elif a < 0 or b < 0:
        return -c
    return 0
