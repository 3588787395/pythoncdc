def f(items, g, log):
    for x in items:
        if x:
            try:
                g(x)
            except BaseException:
                log(x)
