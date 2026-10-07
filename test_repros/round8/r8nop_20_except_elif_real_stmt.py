def n8p20(a, log):
    try:
        k(a)
    except Exception as e:
        if log:
            if a:
                log.info(e)
            elif a is None:
                flag = 1
            else:
                log.warn(e)
                flag = 1
