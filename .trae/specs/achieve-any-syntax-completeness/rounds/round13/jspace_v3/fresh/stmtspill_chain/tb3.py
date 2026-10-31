def f(m, opt):
    w = dict(m)
    r = wrap(a=m or w, b=opt or 'z', c=opt or m)
    return r
