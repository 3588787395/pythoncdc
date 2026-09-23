def w(a, b, c, d, log, g):
    if not g():
        log.info('s {s} i {i}'.format(s='p' if c else ('q' if d else 'r'), i=a))
    return a
