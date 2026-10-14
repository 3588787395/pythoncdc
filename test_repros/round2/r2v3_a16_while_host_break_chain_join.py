# round-2 r2v3 specimen (synthetic, minimal)
def f(flag, redata, stop):
    while not stop:
        if stop.x:
            break
        if flag == 1:
            log('a')
        elif flag == -1:
            log('b')
        return redata
    if redata:
        log('x')
