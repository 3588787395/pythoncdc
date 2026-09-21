def f(cond, d, e):
    while cond:
        if cond:
            d = 1
        elif d:
            d = d + 1
            if d < e:
                e = d
        cond = False
    return (d, e)
