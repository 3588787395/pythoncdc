def r6_g1_forhost_ctl(items, flag, q):
    for it in items:
        if flag:
            while len(q) > 0:
                if len(q) == 0:
                    pass
                work(q)
        tail(it)
