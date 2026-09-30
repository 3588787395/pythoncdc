# Source Generated with Decompyle++ (Python version)
# File: r39w_witness.pyc (Python 3.11)

def ctl_two_cont(d, ks):
    for k in ks:
        try:
            if k > 3:
                d[k] = 1
                continue
            elif k < 0:
                d[k] = -1
            continue
        except Exception:
            pass
    return d
