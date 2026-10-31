def f(items):
    out = 0
    i = 0
    while i < len(items):
        d = items[i]
        if d is None:
            i += 1
            continue
        elif d < 0:
            break
        out += d
        i += 1
    return out
