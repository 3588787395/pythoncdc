def f(items, g):
    for x in items:
        g(x)
        if x:
            if x > 1:
                continue
