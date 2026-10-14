def n8p15(a, log):
    try:
        k(a)
    except Exception as e:
        if log:
            if a:
                log.info(e)
            elif a is None:
                pass
            else:
                log.warn(e)
                flag = 1
