def f(items, g, h):
    for x in items:
        if x:
            g(x)
        elif x > 1:
            h(x)
