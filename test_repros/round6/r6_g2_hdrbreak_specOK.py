# Source Generated with Decompyle++ (Python version)
# File: r6_g2_hdrbreak_spec.pyc (Python 3.11)

def r6_g2_hdrbreak_spec(cond, q, status):
    while len(q) > 0:
        try:
            lock.acquire()
            item = q.pop(0)
        finally:
            lock.release()
        if item is None:
            return None
        elif status in (STOP, DELETE):
            log('bad status')
            continue
        handle(item)
