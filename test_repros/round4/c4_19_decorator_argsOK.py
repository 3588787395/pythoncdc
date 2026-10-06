# Source Generated with Decompyle++ (Python version)
# File: c4_19_decorator_args.pyc (Python 3.11)

def deco(n):
    def wrap(f):
        def inner(*a, **k):
            return f(*(a), **(k))
        return inner
    return wrap
@deco(1)
def e01(x):
    return x
@deco(2)
@deco(3)
def e02(x):
    return x + 1
class CD:
    @deco(4)
    def m(self, x):
        return x
def e03_shallow(x):
    return x
def e04_deep(f):
    @deco(f(1))
    def inner():
        return 1
    return inner
def e05_closure(x):
    def outer():
        @deco(x)
        def inner():
            return x
        return inner
    return outer()
def e06_nested_deco():
    @deco(deco(1)(lambda y: y)(2))
    def inner():
        return 0
    return inner
class CD2:
    @deco(5)
    @staticmethod
    def s(x):
        return x
    @deco(6)
    @property
    def p(self):
        return self.v
@deco(7)
class CD3:
    pass
def e07_stack(x):
    @deco(x)
    @deco(x + 1)
    @deco(x + 2)
    def inner():
        return x
    return inner
def e08_async():
    @deco(8)
    async def inner():
        return 1
    return inner
def e09_method_local(x):
    class Local:
        @((x,))
        def m(self):
            return x
    return Local
