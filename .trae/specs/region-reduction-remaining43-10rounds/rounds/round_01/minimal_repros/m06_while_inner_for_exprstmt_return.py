def f(items):
    while items:
        a = items.pop()
        for b in a:
            if b < 0:
                continue
        log.info('x')
        return a
