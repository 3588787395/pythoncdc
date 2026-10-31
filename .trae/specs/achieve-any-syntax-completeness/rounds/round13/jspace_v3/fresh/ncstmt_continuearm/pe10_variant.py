def f(items):
    out = 0
    for x in items:
        d = x.get('k')
        if d is None:
            out += 1
            continue
        out += d
    return out
