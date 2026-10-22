# Source Generated with Decompyle++ (Python version)
# File: cp_decorator_order.pyc (Python 3.11)

def d1(f):
    return f
def d2(f):
    return f
@d2
@d1
def g():
    return 1
