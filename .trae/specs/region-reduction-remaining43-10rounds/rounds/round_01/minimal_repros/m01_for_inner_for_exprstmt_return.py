def f(items):
    for a in items:
        acc = {}
        for b in a:
            if b == 0:
                continue
            acc[b] = 1
        msg = 'done'
        log.info(msg)
        return acc
