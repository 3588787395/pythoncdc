# Source Generated with Decompyle++ (Python version)
# File: r5v5_12_decorator_cross.pyc (Python 3.11)

def deco(n):
    def wrap(f):
        def inner(*a, **k):
            return f(*(a), **(k))
        return inner
    return wrap
@deco(1)
def d_root(x):
    return x
@deco(2)
class DClass:
    @deco(3)
    def m(self, x):
        return x
    @deco(4)
    @staticmethod
    def s(x):
        return x
    @deco(5)
    @property
    def p(self):
        return self.v
def d_deep(x):
    class Local:
        @((x,))
        def m(self):
            return x
    return Local
def d_closure(x):
    def outer():
        @deco(x)
        def inner():
            return x
        return inner
    return outer()
def d_stack(x):
    @deco(x)
    @deco(x + 1)
    @deco(x + 2)
    def inner():
        return x
    return inner
def d_nested_deco():
    @deco(deco(1)(lambda y: y)(2))
    def inner():
        return 0
    return inner
def d_async():
    @deco(6)
    async def inner():
        return 1
    return inner
