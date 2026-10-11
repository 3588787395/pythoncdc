# Source Generated with Decompyle++ (Python version)
# File: r8v8fc_b106_star_battery.pyc (Python 3.11)

def v1(f, xs, ys):
    return f(*xs, *ys)
def v2(f, xs):
    return f(*xs, 1)
def v3(f, xs):
    return f(1, *xs, 2)
def v4(f, xs, d):
    return f(*xs, k=1, **(d))
def v5(f, xs, ys, d):
    return f(1, *xs, *ys, k=2, **(d))
def v6(f, xs):
    return [f(*xs, v) for v in xs]
def v7(f, xs):
    return {f(*xs, v) for v in xs}
def v8(f, k, v):
    return {f(*k, v): f(*k, v + 1) for v in k}
def v9(f, xs):
    return list((f(*xs, v) for v in xs))
def v10(xs):
    g = lambda *a, **kw: (a, kw)
    return g(*xs, m=1)
def v11(f, xs):
    return f(*xs, 1)
def v12(f, gen, xs):
    return f(*gen(), *xs)
