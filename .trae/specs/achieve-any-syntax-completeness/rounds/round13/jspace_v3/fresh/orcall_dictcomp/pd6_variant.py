def f(src, opt):
    cfg = {k: v for k, v in src.items() if v is not None}
    cfg['tag'] = 'x'
    obj = build(kind=opt or 'plain', data=cfg)
    return obj
