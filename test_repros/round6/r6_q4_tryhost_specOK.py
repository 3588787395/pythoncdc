# Source Generated with Decompyle++ (Python version)
# File: r6_q4_tryhost_spec.pyc (Python 3.11)

def r6_q4_tryhost_spec(x):
    try:
        work(x)
    except OSError:
        log('e')
        clean()
    finally:
        clean()
