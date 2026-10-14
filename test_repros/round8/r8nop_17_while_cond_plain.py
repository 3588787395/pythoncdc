def n8p17(a, lim):
    while now() - a <= lim:
        if step(a):
            break
    return a
