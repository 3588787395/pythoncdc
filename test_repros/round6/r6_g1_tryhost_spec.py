def r6_g1_tryhost_spec(flag, q):
    try:
        if flag:
            while True:
                if len(q) == 0:
                    continue
                work(q)
    except OSError:
        log('bad')
