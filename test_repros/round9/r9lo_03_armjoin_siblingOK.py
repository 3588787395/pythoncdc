# Source Generated with Decompyle++ (Python version)
# File: r9lo_03_armjoin_sibling.pyc (Python 3.11)

def r9lo_03_armjoin_sibling(trade_account, trade_id):
    count = 1
    current_time = datetime.datetime.now()
    reconnect_flag = False
    while True:
        error_dict, response = trade_account.reconnect({})
        if error_dict['error_no'] == 0:
            reconnect_flag = True
            login_semaphore.release()
        elif get_trade_status(trade_id) == TradeStatus.TRADE_STOP:
            pass
        else:
            strategy_log.error('login failed')
            count += 1
            time.sleep(LOGIN_FREQUENCY)
            continue
        if reconnect_flag is False:
            strategy_log.error('closing')
            set_trade_stop_status(trade_id)
        return reconnect_flag
