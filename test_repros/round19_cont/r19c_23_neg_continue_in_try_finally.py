def f(items, g):
    for x in items:
        try:
            if x:
                continue
            g(x)
        finally:
            g(0)
