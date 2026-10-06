def f(symbols, mk):
    res = mk(0)
    for s in symbols:
        if s:
            res = mk(s)
            break
    else:
        res = mk(-1)
    return res
