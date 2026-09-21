def f(items, g, h):
    for x in items:
        if x:
            g(0)
        else:
            try:
                g(x)
            except BaseException:
                h(x)
