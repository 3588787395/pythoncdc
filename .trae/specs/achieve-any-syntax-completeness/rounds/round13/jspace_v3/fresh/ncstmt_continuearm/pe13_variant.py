def f(items, limit):
    out = 0
    i = 0
    while i < len(items):
        d = items[i]
        if d > limit:
            i += 1
            continue
        out += d
        i += 1
    return out
