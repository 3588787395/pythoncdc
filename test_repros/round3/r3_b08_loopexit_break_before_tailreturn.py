def f(a, syms, x):
    res = None
    if a:
        res = mk(1)
    for s in syms:
        if s:
            res = mk(2)
            break
        use(s)
    return res
