# Source Generated with Decompyle++ (Python version)
# File: r6_g1_tickloop_ctl2.pyc (Python 3.11)

def r6_g1_tickloop_ctl2(before_start, q):
    while not before_start:
        nap(60)
    if before_start:
        if len(q) == 0:
            pass
        else:
            work(q)
