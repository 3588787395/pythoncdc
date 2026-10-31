def f(items):
    out = 0
    i = 0
    while i < len(items):
        if items[i] is None:
            i += 1
            continue
        out += 1
        i += 1
    return out
