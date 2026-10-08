def f(cfg, freq, ph):
    dt = 0
    if cfg == '1m' and freq == '1d' or ph == 1:
        dt = 2
    return dt
