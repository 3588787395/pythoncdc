def r6_g2_hdrbreak_ctl(cond, q, status):
    while len(q) > 0:
        try:
            lock.acquire()
            item = q.pop(0)
        finally:
            lock.release()
        if item is None:
            break
        handle(item)
    else:
        nap(1)
