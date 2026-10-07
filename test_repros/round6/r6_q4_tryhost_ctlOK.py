# Source Generated with Decompyle++ (Python version)
# File: r6_q4_tryhost_ctl.pyc (Python 3.11)

def r6_q4_tryhost_ctl(x):
    try:
        work(x)
    except OSError:
        log('e')
    finally:
        clean()
