class A:
    def __enter__(self):
        return self
    def __exit__(self, *a):
        return False
class B(A):
    pass
def f():
    with A() as a, B() as b:
        return 1
