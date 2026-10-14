def b121_03(q, log, ex):
    while True:
        try:
            d = q.get(5)
            if d == SENTINEL:
                return None
            else:
                touch(d)
        except BaseException as e:
            if log:
                log.err(e)
            if STOP:
                return None
