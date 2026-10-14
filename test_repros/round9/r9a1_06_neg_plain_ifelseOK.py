# Source Generated with Decompyle++ (Python version)
# File: r9a1_06_neg_plain_ifelse.pyc (Python 3.11)

def r9a1_06_neg_plain_ifelse(q, log, work, done):
    while len(q) > 0:
        x = q.pop(0)
        if bad(x):
            log('bad')
        else:
            work(x)
            done(x)
    sleep(0.001)
