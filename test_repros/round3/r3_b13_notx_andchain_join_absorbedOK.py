# Source Generated with Decompyle++ (Python version)
# File: r3_b13_notx_andchain_join_absorbed.pyc (Python 3.11)

def f(include, freq, qd, am, pm, ac, pc):
    if not include and freq == 1 and qd not in (am, pm) and (qd > ac or qd > pc):
        out = step(qd)
    out2 = tail(qd)
    if include:
        return 7
    else:
        return out2
