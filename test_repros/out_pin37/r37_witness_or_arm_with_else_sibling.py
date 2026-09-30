# Source Generated with Decompyle++ (Python version)
# File: r37_witness_or_arm_with_else_sibling.pyc (Python 3.11)

def s(n):
    return n
def f(dt):
    if dt == 'a':
        if '08:30' <= dt < '08:59' or '12:30' <= dt < '12:59':
            s(1)
        else:
            s(2)
    elif dt == 'b':
        s(4)
    s(0)
