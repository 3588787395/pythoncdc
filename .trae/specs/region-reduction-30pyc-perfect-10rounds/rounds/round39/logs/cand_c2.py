def c2(d, ks):
    for k in ks:
        try:
            if k > 3:
                d[k] = 1
                continue
            elif k < 0:
                d[k] = -1
                continue
            continue
        except Exception:
            pass
    return d
