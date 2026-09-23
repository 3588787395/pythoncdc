def w(a, b, c, log, g):
    if not g():
        log.info('i {i} s {s}'.format(a, b))
    return a
