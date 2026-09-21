def f(items, g, h, opener):
    for x in items:
        if x:
            with opener(x) as k:
                try:
                    g(k)
                except BaseException:
                    h(x)
