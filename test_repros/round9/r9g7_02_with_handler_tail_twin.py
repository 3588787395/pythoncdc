def g7_02(lock, log, ex):
    try:
        with CM(lock):
            do(work)
    except Exception as e:
        log.info(e)
