def f(cond, syms, x):
    if cond:
        for s in syms:
            use(s)
            break
    else:
        x = mk(1)
    return x
