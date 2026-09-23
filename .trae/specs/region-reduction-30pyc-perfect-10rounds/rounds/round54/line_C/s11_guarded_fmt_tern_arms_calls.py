def w(a, b, c, log, g, p, q):
    if not g():
        log.info('s {s}'.format(s=p(a) if c else q(a)))
    return a
