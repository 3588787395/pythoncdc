def r6_g1_tickloop_ctl(before_start, q):
    while True:
        while not before_start:
            nap(60)
        if before_start:
            while True:
                if len(q) == 0:
                    pass
                work(q)
