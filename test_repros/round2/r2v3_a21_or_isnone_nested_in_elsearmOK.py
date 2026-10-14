# Source Generated with Decompyle++ (Python version)
# File: r2v3_a21_or_isnone_nested_in_elsearm.pyc (Python 3.11)

def f(k, fq, ex, side):
    if side:
        k = prep(k)
    else:
        k = prep2(k)
    if not fq is not None or ex is None:
        return k
    else:
        names = list(ex)
        build(names, k)
        return k
