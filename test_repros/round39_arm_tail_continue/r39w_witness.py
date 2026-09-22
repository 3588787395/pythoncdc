def ctl_two_cont(d, ks):
    for k in ks:
        try:
            if k > 3:
                d[k] = 1
                continue
            if k < 0:
                d[k] = -1
                continue
        except Exception:
            pass
    return d
