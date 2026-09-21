def f(items, g):
    for x in items:
        if x:
            continue
        g(x)
