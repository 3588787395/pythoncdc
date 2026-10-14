# Source Generated with Decompyle++ (Python version)
# File: r6_g2_hdrbreak_ctl.pyc (Python 3.11)

def r6_g2_hdrbreak_ctl(cond, q, status):
    while len(q) > 0:
        try:
            lock.acquire()
            item = q.pop(0)
        finally:
            lock.release()
        if item is None:
            return None
        handle(item)
    nap(1)
    return None
