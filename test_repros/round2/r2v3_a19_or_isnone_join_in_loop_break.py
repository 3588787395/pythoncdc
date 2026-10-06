# round-2 r2v3 specimen (synthetic, minimal)
def f(a, b, redata, n):
    for i in n:
        if i:
            break
        if a is None or b is None:
            return redata
        use(a, b)
    if redata:
        log('x')
