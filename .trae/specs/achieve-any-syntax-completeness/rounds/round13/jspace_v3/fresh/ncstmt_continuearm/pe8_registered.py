def f(items):
    out = 0
    i = 0
    while i < len(items):
        d = items[i]
        if d is not None:
            out += d
            i += 1
            continue
        break
    return out
