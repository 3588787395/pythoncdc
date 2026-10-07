def n8p06(log, ex):
    try:
        k(log)
    except Exception as e:
        if log:
            if ex:
                log.backtest.info(e)
            elif not ex:
                log.trade.info(e)
