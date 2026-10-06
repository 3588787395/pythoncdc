# Source Generated with Decompyle++ (Python version)
# File: r2v3_a10_kline_nested_control.pyc (Python 3.11)

def f(kline, fq, ex_info):
    if fq is None:
        return kline
    elif ex_info is None:
        return kline
    else:
        names = list(ex_info)
        build(names, kline)
        return kline
