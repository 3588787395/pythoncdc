def f97(flag, code, log):
    if flag in (1, 2):
        if code == 0:
            log('a')
        else:
            log('b')
            return None
        if code == 1:
            log('c')
    else:
        if code == 2:
            log('d')
    log('tail')
