def b121_02(lock, log, ex):
    try:
        with CM(lock):
            do(work)
    except Exception as e:
        if log:
            if ex:
                log.a.info(e)
            elif ex:
                log.b.info(e)
