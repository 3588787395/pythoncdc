def n8p21(a, lim, log):
    count = 1
    while now() - a <= lim:
        if g(count) and count:
            count += 1
        else:
            log.error(count)
            continue
        return count
