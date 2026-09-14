def f(items):
    for a in items:
        for b in a:
            for c in b:
                if c:
                    continue
        log.info('deep')
        return a
