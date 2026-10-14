# Source Generated with Decompyle++ (Python version)
# File: r6_g1_forhost_ctl.pyc (Python 3.11)

def r6_g1_forhost_ctl(items, flag, q):
    for it in items:
        while flag and len(q) > 0:
            if len(q) == 0:
                pass
            work(q)
        tail(it)
