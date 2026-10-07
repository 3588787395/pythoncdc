def r6_g1_forhost_spec(items, flag, q):
    for it in items:
        if flag:
            while True:
                if len(q) == 0:
                    continue
                work(q)
        tail(it)
