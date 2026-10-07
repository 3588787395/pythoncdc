def b121_03(log, ex):
    try:
        k(log)
    except ValueError as e:
        if log:
            log.a.info(e)
    except TypeError as e:
        if log:
            log.b.info(e)
