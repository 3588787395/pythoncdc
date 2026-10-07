# Source Generated with Decompyle++ (Python version)
# File: r6_g1_tryhost_ctl.pyc (Python 3.11)

def r6_g1_tryhost_ctl(flag, q):
    try:
        if flag:
            while len(q) == 0:
                break
            work(q)
        else:
            return None
    except OSError:
        log('bad')
        return None
