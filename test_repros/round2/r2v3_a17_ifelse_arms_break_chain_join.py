# round-2 r2v3 specimen (synthetic, minimal)
def f(flag, redata, n):
    for i in n:
        if i:
            break
        if flag == 1:
            log('a')
        else:
            log('b')
        return redata
    if redata:
        log('x')
