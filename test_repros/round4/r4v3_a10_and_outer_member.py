def f(symbol, count, qd, freq, inc):
    nd = int(ts())
    q1 = qd // 100
    if q1 == int(nd) and q1 > 930:
        if freq == 1 and inc:
            rd = get_daily(symbol)
        elif q1 <= 1130 and q1 >= 1000:
            rd = get_min(symbol)
        elif q1 >= 1300 or q1 <= 1500:
            rd = get_tick(symbol)
        else:
            rd = None
        return rd
    return get_history_df(symbol, count, qd, freq)
