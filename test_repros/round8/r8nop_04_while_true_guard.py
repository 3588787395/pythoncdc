def n8p04(a, lim):
    count = 1
    while True:
        if tick() - a <= lim:
            if g(count):
                break
            count += 1
        else:
            break
    return count
