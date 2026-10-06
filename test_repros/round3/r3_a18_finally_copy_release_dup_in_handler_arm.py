def f(s, u):
    s.lock.acquire()
    try:
        for m in s.q:
            if not m:
                return 2
        return 1
    except BaseException:
        return 2
    finally:
        s.lock.release()
