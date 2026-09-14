def f(items):
    try:
        for a in items:
            acc = {}
            for b in a:
                if b == 0:
                    continue
                acc[b] = b
            msg = 'ok %s' % a
            log.info(msg)
            return acc
        return None
    except BaseException:
        log.error('boom')
        return None
