def r9a1_01_backentry_looparm(q, log, work, done):
    while True:
        if len(q) > 0:
            x = q.pop(0)
            if bad(x):
                log('bad')
                continue
            try:
                work(x)
                if x.kind:
                    log('kind')
                    continue
                done(x)
            except ValueError:
                log('err')
                continue
        sleep(0.001)
    return x
