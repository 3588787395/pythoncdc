def lam_root(x):
    f = lambda a: a + x
    return f


class CLam:
    V = 1
    f = lambda self: self.V

    def m(self, xs):
        g = lambda a, b=2: a + b
        return [g(v) for v in xs]


def lam_default(x):
    return lambda a, b=x, *args, **kw: a + b


def lam_comp(xs):
    return [(lambda v: v * 2)(x) for x in xs]


def lam_deep(x, ys):
    return [[(lambda a: a + y)(x) for y in ys] for _ in range(2)]


def lam_star(xs):
    f = lambda *a: a
    return f(*xs)


def lam_boolop(a, b):
    f = lambda: (a or b) and a
    return f


def lam_nested(x):
    f = lambda y: (lambda z: z + y)(x)
    return f


def lam_closure(x):
    def outer():
        return lambda: x + 1
    return outer()
