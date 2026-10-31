def f(items, limit):
    first = None
    for x in items:
        if x is None:
            continue
        elif x > limit:
            first = x
            break
        first = x
    return first
