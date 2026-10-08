def r9w16_12_after_join_stmts(q, log):
    while True:
        if len(q) > 0:
            log(q.pop(0))
        sleep(0.001)
    log('left')
