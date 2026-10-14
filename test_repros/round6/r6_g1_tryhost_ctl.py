def r6_g1_tryhost_ctl(flag, q):
    try:
        if flag:
            while True:
                if len(q) == 0:
                    pass
                work(q)
    except OSError:
        log('bad')
