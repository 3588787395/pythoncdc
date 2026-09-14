def trade_logs_control_pattern(LOG_SWITCH, TRADE_LOG_CONTROL):
    flag = 0
    remove_date = None
    while True:
        size = get_size()
        if size > int(TRADE_LOG_CONTROL) * 1024 * 1024 and flag == 0:
            log('uninstalling')
            remove_date = 'today'
            flag = 1
        if remove_date is not None and remove_date != 'today':
            log('reinstalling')
            remove_date = None
            flag = 0
        if LOG_SWITCH == '1':
            continue
