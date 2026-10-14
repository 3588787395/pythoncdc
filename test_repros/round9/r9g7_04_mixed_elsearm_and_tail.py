def g7_04(lock, log, bars):
    if bars:
        if log:
            return bars[0]
        else:
            return None
    try:
        with CM(lock):
            do(work)
    except Exception as e:
        log.info(e)
