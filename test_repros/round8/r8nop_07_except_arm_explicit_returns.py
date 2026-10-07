def n8p07(log, ex):
    try:
        k(log)
    except Exception as e:
        if log:
            if ex:
                log.backtest.info(e)
                return None
            else:
                log.trade.info(e)
                return None
        else:
            return None
    return None
