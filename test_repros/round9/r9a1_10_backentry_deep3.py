def r9a1_10_backentry_deep3(q, log, work, done):
    while True:
        if len(q) > 0:
            x = q.pop(0)
            if bad(x):
                log('bad')
                continue
            for y in x.rows:
                if y.flag:
                    if y.deep:
                        if y.deeper:
                            log('deepest')
                            continue
                        work(y)
                    log('mid')
                    continue
                done(y)
        sleep(0.001)
    return x
