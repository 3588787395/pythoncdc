def f(items):
    n = 0
    for x in items:
        if x < 0:
            n += 1
            continue
        elif x == 0:
            n += 2
            continue
        n += 3
    return n
