def f(items):
    out = None
    for x in items:
        d = x.get('k')
        if d is not None:
            if isinstance(d, int):
                out = d
                break
            elif d > 2:
                out = d
                continue
    return out
