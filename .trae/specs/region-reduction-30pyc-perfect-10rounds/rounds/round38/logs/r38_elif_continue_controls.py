def ctl_plain_elif(x):
    for i in x:
        if i > 3:
            a = 1
        elif i < 0:
            a = 2
        print(a)
    return 0
def ctl_single_cont(d, ks):
    for k in ks:
        if k > 3:
            d[k] = 1
            continue
    return d
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
def ctl_elif_more_body(d, ks):
    for k in ks:
        if k > 3:
            d[k] = 1
        elif k < 0:
            d[k] = -1
        d[k + 1] = 2
    return d
