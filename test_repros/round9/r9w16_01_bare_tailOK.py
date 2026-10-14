# Source Generated with Decompyle++ (Python version)
# File: r9w16_01_bare_tail.pyc (Python 3.11)

def r9w16_01_bare_tail(q, log):
    while True:
        if len(q) > 0:
            x = q.pop(0)
            log(x)
        sleep(0.001)
