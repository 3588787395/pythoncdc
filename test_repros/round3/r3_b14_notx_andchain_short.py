def f(include, freq, qd, am, pm, ac, pc):
    if not include and freq == 1 and qd not in (am, pm):
        out = step(qd)
    out2 = tail(qd)
    return out2
