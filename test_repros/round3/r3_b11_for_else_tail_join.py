def f(cond, syms, x):
    for s in syms:
        if cond:
            break
        use(s)
    else:
        x = mk(1)
    return x
