# Source Generated with Decompyle++ (Python version)
# File: r2v3_b15_whiletail_break_after_if_arm.pyc (Python 3.11)

def f(stop, TH):
    while not stop:
        from mod import THREAD_STATUS
        if THREAD_STATUS:
            break
        time.sleep(0.01)
