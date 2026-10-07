def n8p22(a, log):
    if log:
        if a:
            log.info(a)
        elif a is None:
            pass
        else:
            log.warn(a)
            flag = 1
