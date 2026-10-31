def f(items):
    total = 0
    i = 0
    while i < len(items):
        d = items[i]
        if d is None:
            i += 2
            total += 1
            continue
        total += d
        i += 1
    return total
