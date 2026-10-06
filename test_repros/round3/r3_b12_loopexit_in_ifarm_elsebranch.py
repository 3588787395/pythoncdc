def f(cond, syms, x):
    if cond:
        for s in syms:
            if s:
                break
            use(s)
    else:
        x = mk(1)
    return x
