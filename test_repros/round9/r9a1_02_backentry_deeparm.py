def r9a1_02_backentry_deeparm(q, log, work, done):
    while True:
        if len(q) > 0:
            for x in q:
                if check(x):
                    log('skip')
                    continue
                work(x)
                if x.a:
                    if x.b:
                        log('deep')
                        continue
                    done(x)
                else:
                    log('else')
                    continue
        sleep(0.001)
    return x
