def r9a1_05_pastconfluence_share(q, log, work):
    while len(q) > 0:
        if q[0].flag:
            if q[0].removed:
                continue
        work(q)
        q.pop(0)
    return 1
