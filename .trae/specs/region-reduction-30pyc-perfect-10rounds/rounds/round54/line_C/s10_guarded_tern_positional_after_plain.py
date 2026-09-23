def w(a, b, c, d, log, g):
    if not g():
        log.info('i {i} s {s} o {o}'.format(a, b, 'p' if c else 'q'))
    return a
