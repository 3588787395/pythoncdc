def f(a, d, e):
    if a:
        d = 1
    elif d:
        d = d * 2
        if d < e:
            e = d
    return (d, e)
