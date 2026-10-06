# Source Generated with Decompyle++ (Python version)
# File: g4_import_hosts3.pyc (Python 3.11)

from . import m0
def f(xs):
    a, b = 1, 2
    from . import m1
    return (a, b, m1)
def g(xs):
    p, q = xs
    from .sub import m2 as z
    return (p, q, z)
def h(xs):
    a, (b, c) = xs
    from ..deep import m3
    return (a, b, c, m3)
class C:
    x, y = 1, 2
    def m(self):
        a, *b = [1, 2, 3]
        from .pkg import m4
        return (a, b, m4)
def k(xs):
    a = b = 5
    from .q import m5
    return (a, b, m5)
