from . import m0


def f():
    from . import m1
    return m1


class C:
    from .sub import m2

    def m(self):
        from ..pkg import m3
        return m3


def g(cond, xs):
    r = []
    for i in range(2):
        from . import m4
        r.append(m4)
    while cond:
        from .y import m6
        r.append(m6)
        cond = False
    with open('f') as fh:
        from .z import m7
        r.append(m7)
    try:
        from .t import m8
        r.append(m8)
    finally:
        from .u import m9
    if cond:
        from .x import m5
        r.append(m5)
    return r