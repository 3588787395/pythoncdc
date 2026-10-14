# Source Generated with Decompyle++ (Python version)
# File: r6_g2_twoloop_spec.pyc (Python 3.11)

def r6_g2_twoloop_spec(ts, cur):
    while ts != cur:
        cur = read(ts)
        ts = cur
        if cur == PAUSE:
            emit(cur)
            continue
        if cur == STOP:
            return 1
        emit2(cur)
    nap(5)
    return None
