from . import m0

_V = 1


def h(xs):
    r = []
    try:
        xs.append(1)
    except ValueError:
        from .e import m10
        r.append(m10)
    except KeyError as k:
        from .f import m11
        r.append(m11)
    return r


def i(xs):
    r = []
    for x in xs:
        try:
            from .g import m12
            r.append(m12)
        except Exception:
            from .h import m13
            r.append(m13)
    return r


def j(n):
    r = []
    for a in range(n):
        for b in range(a):
            from ..deep import m14
            r.append(m14)
    return r


class K:
    def m(self):
        try:
            from .k import m15
        finally:
            from .l import m16
        return m15


def l(xs):
    with open('a') as f:
        with open('b') as g:
            from .m import m17
            xs.append((f, g, m17))
    return xs


_y = m0.attr if _V else None