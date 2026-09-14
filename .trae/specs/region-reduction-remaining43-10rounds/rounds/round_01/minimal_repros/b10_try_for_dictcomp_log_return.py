def f(items):
    try:
        for a in items:
            acc = {b: b for b in a}
            log.info('x')
            return acc
        return None
    except BaseException:
        return None
