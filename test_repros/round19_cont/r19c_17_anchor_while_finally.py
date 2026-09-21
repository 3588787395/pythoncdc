def f(cond, g):
    while cond:
        cond -= 1
        if cond:
            try:
                g(cond)
            finally:
                g(0)
