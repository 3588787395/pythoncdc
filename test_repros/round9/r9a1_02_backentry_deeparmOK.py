# Source Generated with Decompyle++ (Python version)
# File: r9a1_02_backentry_deeparm.pyc (Python 3.11)

def r9a1_02_backentry_deeparm(q, log, work, done):
    while len(q) > 0:
        for x in q:
            if check(x):
                log('skip')
                continue
            work(x)
            if x.a:
                if x.b:
                    log('deep')
                    continue
                done(x)
                continue
            log('else')
        sleep(0.001)
        continue
