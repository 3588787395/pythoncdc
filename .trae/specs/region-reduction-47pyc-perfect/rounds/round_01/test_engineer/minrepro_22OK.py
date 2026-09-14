# Source Generated with Decompyle++ (Python version)
# File: minrepro_22.pyc (Python 3.11)

def trade_logs_control_pattern(LOG_SWITCH, TRADE_LOG_CONTROL):
    flag = 0
    remove_date = None
    while True:
        size = get_size()
        if size > int(TRADE_LOG_CONTROL) * 1024 * 1024:
            if flag == 0:
                log('uninstalling')
                remove_date = 'today'
                flag = 1
        elif remove_date is not None and remove_date != 'today':
            log('reinstalling')
            remove_date = None
            flag = 0
        if LOG_SWITCH == '1':
            continue
