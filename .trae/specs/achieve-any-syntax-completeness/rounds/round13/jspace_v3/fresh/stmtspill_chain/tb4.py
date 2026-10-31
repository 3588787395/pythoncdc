def f(m, opt):
    w = dict(m)
    r = wrap(payload=m or w, tag=opt or 'z')
    w['k'] = r
    return w
