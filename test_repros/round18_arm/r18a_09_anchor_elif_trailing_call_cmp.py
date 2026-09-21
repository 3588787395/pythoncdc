def g(x):
    return x


def f(a, d, e):
    if a:
        d = 1
    elif d:
        d = g(d)
        if d < e:
            e = g(d)
    return (d, e)
