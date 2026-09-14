def setup_pattern(LOG_SWITCH, BACKTEST_LOG_CONTROL):
    if LOG_SWITCH == '1':
        handler = (int(BACKTEST_LOG_CONTROL), int(BACKTEST_LOG_CONTROL))
    else:
        handler = (102400, 102400)
    return handler
