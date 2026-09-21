def f(items, g):
    for x in items:
        if x:
            try:
                g(x)
            except ValueError:
                g(x)
