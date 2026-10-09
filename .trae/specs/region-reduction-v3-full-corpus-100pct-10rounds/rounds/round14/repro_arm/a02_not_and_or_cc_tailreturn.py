def f(include, qd, pm_close, am_close, pm_open, engine_obj, symbol):
    if not include:
        if qd > pm_close or am_close < qd <= pm_open:
            return engine_obj.kline(symbol, True)
    return None
