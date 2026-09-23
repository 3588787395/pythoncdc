def w(a, b, c, log, g):
    if not g():
        log.info('i {i} s {s}'.format(i=a, s='p' if c else 'q'))
    return a
