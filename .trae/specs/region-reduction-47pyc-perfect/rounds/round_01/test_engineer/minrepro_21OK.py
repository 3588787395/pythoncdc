# Source Generated with Decompyle++ (Python version)
# File: minrepro_21.pyc (Python 3.11)

def setup_pattern(LOG_SWITCH, BACKTEST_LOG_CONTROL):
    if LOG_SWITCH == '1':
        handler = (int(BACKTEST_LOG_CONTROL), int(BACKTEST_LOG_CONTROL))
    else:
        handler = (102400, 102400)
    return handler
