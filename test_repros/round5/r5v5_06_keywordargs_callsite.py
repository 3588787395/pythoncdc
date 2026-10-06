MOD_KW = _kf(a=1, b=2)
MOD_KW2 = _kf(1, 2, k=3)


def kw_root(f):
    return f(a=1, b=2, c=3)


class CKw:
    V = _kf(k=1)

    def m(self, f):
        return f(self.v, key=self.w, other=2)


def kw_deep(f, g):
    r = 0
    for i in range(3):
        if i:
            r = f(alpha=i, beta=i + 1, gamma=i + 2)
    return r


def kw_nested(f, g):
    return f(g(a=1), b=g(c=2), d=3)


def kw_dict(f):
    return f(b=1, a=2, **{'c': 3})


def kw_closure(f):
    def inner():
        return f(x=1, y=2)
    return inner()


def kw_comp(f, xs):
    return [f(v=v, w=v + 1) for v in xs]


def kw_try(f):
    try:
        return f(a=1)
    finally:
        pass


def kw_match(f, x):
    match x:
        case 0:
            return f(a=1, b=2)
        case _:
            return f(a=0, b=0)


def kw_with(f):
    with open('a') as h:
        return f(a=len(h.name), b=2)
