class A(Exception):
    pass
class B(Exception):
    pass
def f():
    try:
        pass
    except (A, B):
        return 1
