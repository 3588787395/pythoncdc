def f(a, b, d, e):
    if a:
        d = 1
    elif b:
        b = b + 1
        if b < e:
            e = b
    elif d:
        d = d + 2
        if d > e:
            e = d
    return (d, e)
