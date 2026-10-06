# Source Generated with Decompyle++ (Python version)
# File: r3_b14_notx_andchain_short.pyc (Python 3.11)

def f(include, freq, qd, am, pm, ac, pc):
    if not include and freq == 1 and qd not in (am, pm):
        out = step(qd)
    out2 = tail(qd)
    return out2
