def f(items, d, e):
    for a in items:
        if a:
            d = 1
        elif d:
            d = d + 1
            if d < e:
                e = d
    return (d, e)
