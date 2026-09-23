def w(a, b, c, d, log, g):
    if not g():
        log.info('i {i} s {s} o {o} h {h}'.format(i=a, s='p' if c else 'q', o=b, h='r' if d else 's'))
    return a
