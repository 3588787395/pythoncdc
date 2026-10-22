# Source Generated with Decompyle++ (Python version)
# File: cp_with_item_order.pyc (Python 3.11)

class A:
    def __enter__(self):
        return self
    def __exit__(self, *a):
        return False
class B(A):
    pass
def f():
    with B() as a, A() as b:
        return 1
