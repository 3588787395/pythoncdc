# Source Generated with Decompyle++ (Python version)
# File: r9a1_01_backentry_looparm.pyc (Python 3.11)

def r9a1_01_backentry_looparm(q, log, work, done):
    while len(q) > 0:
        x = q.pop(0)
        if bad(x):
            log('bad')
            continue
        break
        try:
            work(x)
            if x.kind:
                log('kind')
            else:
                done(x)
        except ValueError:
            log('err')
            continue
    else:
        sleep(0.001)
