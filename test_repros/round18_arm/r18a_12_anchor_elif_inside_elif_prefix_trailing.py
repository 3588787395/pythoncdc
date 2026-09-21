def f(a, b, d, e):
    if a:
        d = 1
    elif b:
        if d:
            d = d + 1
            if d < e:
                e = d
    return (d, e)
