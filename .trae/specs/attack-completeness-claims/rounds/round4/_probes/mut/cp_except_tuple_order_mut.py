# Source Generated with Decompyle++ (Python version)
# File: cp_except_tuple_order.pyc (Python 3.11)

class A(Exception):
    pass
class B(Exception):
    pass
def f():
    try:
        pass
    except (B, A):
        return 1
