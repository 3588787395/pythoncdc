def f(include, freq, qd, am, pm, ac, pc):
    if not include and freq == 1 and qd not in (am, pm) and (qd > ac or qd > pc):
        out = step(qd)
    out2 = tail(qd)
    if include:
        return 7
    return out2
