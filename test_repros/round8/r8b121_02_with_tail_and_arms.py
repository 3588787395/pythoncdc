def b121_02(lock, log, ex):
    try:
        with CM(lock):
            do(work)
    except Exception as e:
        if log:
            log.info(e)
