def f(d):
    try:
        if d.kind == 1:
            out = build(d.a)
        elif d.kind == 2:
            out = build(d.b)
        else:
            out = None
        return out
    except Exception:
        LOG.error('x')
        return None
