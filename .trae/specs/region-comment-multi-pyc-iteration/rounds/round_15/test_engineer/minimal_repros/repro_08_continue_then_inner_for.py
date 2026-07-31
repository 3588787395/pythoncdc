"""R15 CTRL (fix-validation): get_trading_schedule mirror — continue in then-block.

Pattern: `for ...: if cond: continue; for ...: ...` — the inner for-loop is the
post-if statement (NOT an else-branch). R15 fix detects then_succ ending with
JUMP_BACKWARD to the enclosing loop header (continue) and sets merge=else_succ,
creating IF_THEN so the inner for-loop becomes a post-if statement.

Source pyc: site-packages/IQCommon/trade_schedule.pyc :: get_trading_schedule
Before R15: IF_THEN_ELSE entry=66 merge=64 then=[86] else=[88,132,134] — inner
  for-loop mis-attributed to else branch (dropped as dead code after continue).
After R15: IF_THEN entry=66 merge=88 then=[86] else=[] — correct.
"""
def get_trading_schedule(trading_time, is_backtest=True):
    time_set = set()
    start_time_delta = int(is_backtest)
    for s, e in trading_time:
        if s > 1200:
            continue
        for i in range(s + start_time_delta, e + 1):
            time_set.add(divmod(i, 60))
    return time_set
