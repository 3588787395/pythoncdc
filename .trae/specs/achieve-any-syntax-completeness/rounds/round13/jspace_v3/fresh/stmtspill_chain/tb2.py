def f(m, opt):
    w = dict(m)
    r = wrap(m or w, tag=opt or 'z')
    return r
