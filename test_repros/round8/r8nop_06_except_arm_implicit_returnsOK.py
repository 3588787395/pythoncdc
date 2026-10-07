# Source Generated with Decompyle++ (Python version)
# File: r8nop_06_except_arm_implicit_returns.pyc (Python 3.11)

def n8p06(log, ex):
    try:
        k(log)
        return None
    except Exception as e:
        if log:
            if ex:
                log.backtest.info(e)
            elif not ex:
                log.trade.info(e)
