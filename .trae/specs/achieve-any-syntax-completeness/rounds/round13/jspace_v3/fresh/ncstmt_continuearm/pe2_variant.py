def f(items):
    out = 0
    for x in items:
        if x is None:
            out += 1
            continue
        out += 2
    return out
