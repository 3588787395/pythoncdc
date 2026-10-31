def f(items):
    out = None
    for x in items:
        if isinstance(x, int):
            out = x
            break
        elif x > 2:
            out = x
            continue
    return out
