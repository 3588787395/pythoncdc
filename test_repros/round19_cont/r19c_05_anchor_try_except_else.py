def f(items, g, h):
    for x in items:
        if x:
            try:
                g(x)
            except BaseException:
                h(x)
            else:
                h(0)
