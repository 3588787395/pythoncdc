def r6_g2_twoloop_spec(ts, cur):
    while ts != cur:
        cur = read(ts)
        ts = cur
        if cur == PAUSE:
            emit(cur)
            continue
        if cur == STOP:
            return 1
        emit2(cur)
    else:
        nap(5)
