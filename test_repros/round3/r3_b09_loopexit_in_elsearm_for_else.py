def f(a, syms, x):
    if a:
        res = mk(1)
    else:
        for s in syms:
            use(s)
            if s > 1:
                break
        else:
            res = mk(x)
    return res
