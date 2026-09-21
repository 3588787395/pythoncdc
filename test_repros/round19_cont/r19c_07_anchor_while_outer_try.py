def f(cond, g, h):
    while cond:
        cond = 0
        if cond:
            try:
                g(cond)
            except BaseException:
                h(cond)
