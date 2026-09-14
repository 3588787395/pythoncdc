def f(items):
    for a in items:
        for b in a:
            pass
        log.info('x')
        return a
    return None
