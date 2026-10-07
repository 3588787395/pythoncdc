# Source Generated with Decompyle++ (Python version)
# File: r8nop_07_except_arm_explicit_returns.pyc (Python 3.11)

def n8p07(log, ex):
    try:
        k(log)
    except Exception as e:
        if log:
            if ex:
                log.backtest.info(e)
                return None
            log.trade.info(e)
            return None
        else:
            return None
    return None
