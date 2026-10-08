# Source Generated with Decompyle++ (Python version)
# File: r9w16_09_tail_is_cond.pyc (Python 3.11)

def r9w16_09_tail_is_cond(q, log):
    while True:
        if len(q) > 0:
            x = q.pop(0)
            log(x)
        if q:
            log('idle')
