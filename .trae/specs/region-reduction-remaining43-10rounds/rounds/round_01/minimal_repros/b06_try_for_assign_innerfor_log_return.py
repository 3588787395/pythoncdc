def f(items):
    try:
        for a in items:
            acc = {}
            for b in a:
                acc[b] = b
            log.info('x')
            return acc
        return None
    except BaseException:
        return None
