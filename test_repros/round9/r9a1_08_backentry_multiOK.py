# Source Generated with Decompyle++ (Python version)
# File: r9a1_08_backentry_multi.pyc (Python 3.11)

def r9a1_08_backentry_multi(q, log, work, done):
    while True:
        if len(q) > 0:
            x = q.pop(0)
            if bad(x):
                log('bad')
                continue
            for y in x.items:
                if y.a:
                    log('a')
                    continue
                work(y)
                if y.b:
                    if y.c:
                        log('c')
                        continue
                    done(y)
                    continue
                log('tail')
            sleep(0.001)
        else:
            break
    return x
