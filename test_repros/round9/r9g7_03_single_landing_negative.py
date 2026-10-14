def g7_03(lock, log):
    try:
        return do(work)
    except Exception as e:
        log.info(e)
