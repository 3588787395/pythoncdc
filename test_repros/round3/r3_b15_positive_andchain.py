def f(include, freq, qd):
    if include and freq == 1:
        out = step(qd)
    out2 = tail(qd)
    return out2
