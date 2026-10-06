# Source Generated with Decompyle++ (Python version)
# File: r2v3_a09_kline_or_isnone_join.pyc (Python 3.11)

def f(kline, fq, ex_info):
    if not fq is not None or ex_info is None:
        return kline
    else:
        names = list(ex_info)
        build(names, kline)
        return kline
