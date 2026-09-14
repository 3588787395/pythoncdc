def f(items):
    try:
        for a in items:
            for b in a:
                pass
            log.info('x')
            return a
    except BaseException:
        return None
