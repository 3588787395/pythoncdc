def f(items, g, h):
    for x in items:
        if x:
            continue
        g(x)
        h(x)
