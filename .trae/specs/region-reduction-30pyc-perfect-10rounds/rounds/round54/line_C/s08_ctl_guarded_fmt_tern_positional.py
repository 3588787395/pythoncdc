def w(a, b, c, log, g):
    if not g():
        log.info(b if c else a)
    return a
