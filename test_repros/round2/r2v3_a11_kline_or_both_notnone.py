# round-2 r2v3 specimen (synthetic, minimal)
def f(kline, fq, ex_info):
    if fq is not None and ex_info is not None:
        names = list(ex_info)
        build(names, kline)
    return kline
