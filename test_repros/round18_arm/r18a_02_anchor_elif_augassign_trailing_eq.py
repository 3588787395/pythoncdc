def f(a, d, e):
    if a:
        d = 1
    elif d:
        d += 1
        if d == e:
            e = 0
    return (d, e)
