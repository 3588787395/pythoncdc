"""R15 DEFECT-REPRO: is_stock_trade_time_now mirror.

Pattern: `return A < x < B or C < x < D` — chained compare (JUMP_IF_FALSE_OR_POP)
combined with BoolOp OR (JUMP_IF_TRUE_OR_POP) in a return-expression context.

Source pyc: site-packages/IQCommon/trade_schedule.pyc :: is_stock_trade_time_now
Defect: JUMP_IF_TRUE_OR_POP (BoolOp OR short-circuit) misinterpreted as if-branch,
decomposing the return-expression into multiple if+pass statements.
"""
import datetime
STOCK_AM_OPEN = datetime.time(9, 30)
STOCK_AM_CLOSE = datetime.time(11, 30)
STOCK_PM_OPEN = datetime.time(13, 0)
STOCK_PM_CLOSE = datetime.time(15, 0)


def is_stock_trade_time_now(now=None):
    if now is None:
        now = datetime.datetime.now().time()
    return STOCK_AM_OPEN < now < STOCK_AM_CLOSE or STOCK_PM_OPEN < now < STOCK_PM_CLOSE
