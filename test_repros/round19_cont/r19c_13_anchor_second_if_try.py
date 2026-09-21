def f(items, g, h):
    for x in items:
        g(x)
        if x:
            try:
                g(x)
            except BaseException:
                h(x)
