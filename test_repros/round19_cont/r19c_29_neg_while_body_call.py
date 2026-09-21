def f(cond, g):
    while cond:
        g(cond)
        cond = 0
