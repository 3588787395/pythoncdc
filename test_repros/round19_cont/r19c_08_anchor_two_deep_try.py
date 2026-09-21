def f(rows, g, h):
    for r in rows:
        for c in r:
            if c:
                try:
                    g(c)
                except BaseException:
                    h(c)
