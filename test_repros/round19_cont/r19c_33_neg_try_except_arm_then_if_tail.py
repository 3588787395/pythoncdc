def f(items, g, h):
    for x in items:
        try:
            g(x)
        except BaseException:
            h(x)
        if x:
            g(0)
