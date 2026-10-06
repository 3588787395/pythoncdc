# Source Generated with Decompyle++ (Python version)
# File: r3_a19_handler_own_release_not_folded.pyc (Python 3.11)

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
