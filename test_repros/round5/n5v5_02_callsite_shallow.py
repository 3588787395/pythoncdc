def n_kw(f):
    return f(a=1, b=2)


def n_star(f, xs):
    return f(*xs)


def n_slice(s):
    return s[1:2]


def n_walrus(x):
    return (n := x)
