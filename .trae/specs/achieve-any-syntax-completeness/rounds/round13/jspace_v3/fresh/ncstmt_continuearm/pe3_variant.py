def f(items):
    out = 0
    i = 0
    while i < len(items):
        if items[i] is None:
            i += 1
            continue
        elif items[i] > 2:
            out += items[i]
            break
        i += 1
    return out
