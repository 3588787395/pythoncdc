def r6_g2_twoloop_ctl(ts, cur):
    while ts != cur:
        cur = read(ts)
        ts = cur
        if cur == PAUSE:
            emit(cur)
            continue
        emit2(cur)
    else:
        nap(5)
