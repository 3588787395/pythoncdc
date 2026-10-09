def f(include, qd, pm_close, am_close, pm_open, engine_obj, symbol):
    if not include and (qd > pm_close or am_close < qd <= pm_open):
        real_data = engine_obj.kline(symbol, True)
    last = 1
    return last
