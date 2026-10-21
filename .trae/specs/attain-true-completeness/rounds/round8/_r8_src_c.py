def f(xs, ys, t):
    total = 0
    for v in (xs if t else ys):
        total += v
    return total


def g(xs, ys, t):
    total = 0
    for v in xs:
        total += v
    return total


def h(xs, ys, t):
    total = 0
    if t:
        total = 1
    return total
