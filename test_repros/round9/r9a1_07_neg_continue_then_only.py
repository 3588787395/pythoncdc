def r9a1_07_neg_continue_then_only(q, log, work):
    while True:
        if len(q) > 0:
            x = q.pop(0)
            if x.skip:
                log('skip')
                continue
            work(x)
        sleep(0.001)
    return x
