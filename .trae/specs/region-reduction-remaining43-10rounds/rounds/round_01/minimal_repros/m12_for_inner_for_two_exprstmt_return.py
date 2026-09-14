def f(items):
    for a in items:
        for b in a:
            pass
        log.info('one')
        log.info('two')
        return a
