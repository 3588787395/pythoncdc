def st_root(f, xs):
    return f(*xs)


def st_nontail(f, xs):
    return f(*xs, 1)


def st_mixed(f, xs):
    return f(1, *xs, 2, k=3)


def st_multistar(f, xs, ys):
    return f(*xs, *ys, **{'k': 0})


def st_deep(f, xs, ys):
    r = 0
    for i in range(2):
        if i:
            r = f(*xs, *ys, **{'k': i})
    return r


class CSt:
    def m(self, f, xs):
        for i in range(2):
            if i:
                return f(*xs, self.v)
        return f(*xs)


def st_close(f, xs):
    def inner():
        return f(*xs, *xs)
    return inner()


def st_match(f, xs, x):
    match x:
        case 0:
            return f(*xs)
        case _:
            return f(*xs, 1)


def st_comp(f, xs):
    return [f(*xs, v) for v in xs]
