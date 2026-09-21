def f(items, g):
    for x in items:
        if x:
            return x
        g(x)
