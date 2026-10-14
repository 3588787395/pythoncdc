def n8p16(a, lim, log):
    count = 1
    while now() - a <= lim:
        if g(count) and count:
            count += 1
        elif status(count) is STOP:
            pass
        else:
            log.error(count)
            continue
        return count
