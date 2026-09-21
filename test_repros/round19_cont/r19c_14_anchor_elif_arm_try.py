def f(items, g, h):
    for x in items:
        if x > 1:
            g(1)
        elif x:
            try:
                g(x)
            except BaseException:
                h(x)
