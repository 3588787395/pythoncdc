# round-2 r2v3 specimen (synthetic, minimal)
def f(kline, fq, ex_info):
    if fq is None or ex_info is None:
        return kline
    names = list(ex_info)
    build(names, kline)
    return kline
