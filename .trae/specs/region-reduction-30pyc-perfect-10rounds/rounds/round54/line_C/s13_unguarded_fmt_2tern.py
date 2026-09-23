def w(a, b, c, d, log):
    log.info('i {i} s {s} o {o}'.format(i=a, s='p' if c else 'q', o='r' if d else 's'))
    return a
