"""R15 DEFECT-REPRO: is_future_trade_time_now mirror.

Pattern: `return A < x < B or C < x < D` — chained compare + BoolOp OR in return.
Mirror of is_future_trade_time_now from trade_schedule.pyc.
"""
import datetime
FUTURE_AM_OPEN = datetime.time(9, 0)
FUTURE_AM_CLOSE = datetime.time(11, 30)
FUTURE_PM_OPEN = datetime.time(13, 0)
FUTURE_PM_CLOSE = datetime.time(15, 15)


def is_future_trade_time_now(now=None):
    if now is None:
        now = datetime.datetime.now().time()
    return FUTURE_AM_OPEN < now < FUTURE_AM_CLOSE or FUTURE_PM_OPEN < now < FUTURE_PM_CLOSE
