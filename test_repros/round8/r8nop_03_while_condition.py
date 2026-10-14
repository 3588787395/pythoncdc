def n8p03(a, lim):
    count = 1
    while tick() - a <= lim:
        if g(count):
            break
        count += 1
    return count
