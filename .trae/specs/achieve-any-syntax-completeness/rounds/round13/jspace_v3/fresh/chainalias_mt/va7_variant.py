def f(d, items):
    for x in items:
        d[x] = alias = x
        if alias:
            break
    return alias
