def f(a, b, d, e):
    if a:
        d = 1
    elif b:
        d = 2
    elif d:
        d = d * 2
        if d < e:
            e = d
    return (d, e)
