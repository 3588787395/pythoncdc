def b121_04(log, ex):
    try:
        k(log)
    except Exception as e:
        if log:
            if ex:
                log.a.info(e)
                return None
            else:
                log.b.info(e)
                return None
        else:
            return None
    return None
