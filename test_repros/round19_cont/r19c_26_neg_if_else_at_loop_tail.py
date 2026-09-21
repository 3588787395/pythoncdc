def f(items, g, h):
    for x in items:
        if x:
            g(x)
        else:
            h(x)
