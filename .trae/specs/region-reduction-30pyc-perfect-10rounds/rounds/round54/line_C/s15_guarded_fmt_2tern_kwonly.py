def w(a, b, c, d, log, g):
    if not g():
        log.info('s {s} o {o}'.format(s='p' if c else 'q', o='r' if d else 's'))
    return a
