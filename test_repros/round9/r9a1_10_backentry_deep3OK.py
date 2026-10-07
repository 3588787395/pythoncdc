# Source Generated with Decompyle++ (Python version)
# File: r9a1_10_backentry_deep3.pyc (Python 3.11)

def r9a1_10_backentry_deep3(q, log, work, done):
    while len(q) > 0:
        x = q.pop(0)
        if bad(x):
            break
        for y in x.rows:
            if y.flag:
                if y.deep:
                    if y.deeper:
                        log('deepest')
                        continue
                    work(y)
                log('mid')
            done(y)
        sleep(0.001)
