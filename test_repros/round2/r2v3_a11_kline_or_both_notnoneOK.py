# Source Generated with Decompyle++ (Python version)
# File: r2v3_a11_kline_or_both_notnone.pyc (Python 3.11)

def f(kline, fq, ex_info):
    if fq is not None and ex_info is not None:
        names = list(ex_info)
        build(names, kline)
    return kline
