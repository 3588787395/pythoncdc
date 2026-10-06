# round-2 r2v3 specimen (synthetic, minimal)
def f(k, fq, ex, side):
    if side:
        k = prep(k)
    else:
        k = prep2(k)
    if fq is None or ex is None:
        return k
    names = list(ex)
    build(names, k)
    return k
