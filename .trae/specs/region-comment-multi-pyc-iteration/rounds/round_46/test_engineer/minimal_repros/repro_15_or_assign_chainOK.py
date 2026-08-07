# Source Generated with Decompyle++ (Python version)
# File: repro_15_or_assign_chain.pyc (Python 3.11)

def func(x, y):
    a = None
    if y:
        a = a or x.get(y)
        b = a
    return b
