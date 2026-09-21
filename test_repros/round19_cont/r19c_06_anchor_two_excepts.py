def f(items, g, h):
    for x in items:
        if x:
            try:
                g(x)
            except ValueError:
                h(x)
            except TypeError:
                h(0)
