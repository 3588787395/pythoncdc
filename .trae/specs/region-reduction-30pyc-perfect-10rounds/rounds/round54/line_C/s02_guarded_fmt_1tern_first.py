def w(a, b, c, log, g):
    if not g():
        log.info('i {i} s {s}'.format(s='p' if c else 'q', i=a))
    return a
