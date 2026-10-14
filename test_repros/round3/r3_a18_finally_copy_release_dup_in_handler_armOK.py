# Source Generated with Decompyle++ (Python version)
# File: r3_a18_finally_copy_release_dup_in_handler_arm.pyc (Python 3.11)

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
