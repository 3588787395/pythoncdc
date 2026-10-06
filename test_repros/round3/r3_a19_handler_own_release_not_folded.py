def h(s, u):
    s.lock.acquire()
    try:
        for m in s.q:
            s.w.append(m)
        return 1
    except BaseException:
        s.lock.release()
        return 2
    finally:
        s.lock.release()
