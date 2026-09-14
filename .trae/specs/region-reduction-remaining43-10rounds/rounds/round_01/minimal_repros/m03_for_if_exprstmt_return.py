def f(items):
    for a in items:
        if a == 0:
            continue
        msg = 'ok'
        log.info(msg)
        return a
