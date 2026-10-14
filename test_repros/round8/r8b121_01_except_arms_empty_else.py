def b121_01(log, ex):
    try:
        k(log)
    except Exception as e:
        if log:
            if ex:
                log.a.info(e)
            elif ex:
                log.b.info(e)
