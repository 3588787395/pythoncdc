def f(items):
    for a in items:
        acc = {}
        for b in a:
            acc[b] = 1
        log.info(acc)
        return acc
