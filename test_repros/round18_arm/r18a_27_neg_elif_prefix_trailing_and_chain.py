def f(a, d, e):
    if a:
        d = 1
    elif d:
        d = d + 1
        if d and d < e:
            e = d
    return (d, e)
