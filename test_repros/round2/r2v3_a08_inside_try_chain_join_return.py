# round-2 r2v3 specimen (synthetic, minimal)
def f(flag, redata):
    try:
        if flag == 1:
            log('a')
        elif flag == -1:
            log('b')
        return redata
        log('after')
    except ValueError:
        return None
