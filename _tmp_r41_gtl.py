def get_trade_list(user_id, op_station=None, strategy_type=None, mode=None):
    """
    查询交易文件信息
    
    :param user_id: 用户ID
    :type user_id: str
    :param op_station: 站点信息
    :type op_station: str
    :param strategy_type: 策略类型。1.传实际策略类型时返回对应的交易信息；
                                  2.传入"trade"时返回交易状态为"0"或"5"的交易信息；
                                  3.传入"current_trade"时返回交易状态为"0"或"5"且ip等于当前服务器IP的交易信息；
                                  4.传入"strategy_active_deleted"时返回交易状态为"0"（运行中）、"2"（删除）或"5"（待重启）的交易信息，
                                    包含已删除交易，且仅返回channel_type为"app"的交易，
                                    对于backtestContentId相同的交易只保留最后一条；
    :type strategy_type: str
    :return: 交易信息
    :rtype: dict
    """
    trade_list_file = os.path.join(TRADE_DIR_PATH, user_id, SIM_TRADING_LIST_FILE)
    delete_trade_list_file = os.path.join(TRADE_DIR_PATH, user_id, DELETE_SIM_TRADING_LIST_FILE)
    trades = []
    try:
        if strategy_type == 'strategy_active_deleted' and os.path.exists(delete_trade_list_file):
            try:
                with FileLock(delete_trade_list_file, mode='shared'):
                    delete_csv_reader = FileIO(delete_trade_list_file).read(return_type='dict_reader')
                for item in delete_csv_reader:
                    if item['status'] == '2':
                        trades.append(item)
            except BaseException:
                app_log.error(f'读取{delete_trade_list_file!s}文件失败，错误原因：{get_traceback_message()!s}')
            else:
                if os.path.exists(trade_list_file):
                    with FileLock(trade_list_file, mode='shared'):
                        csv_reader = FileIO(trade_list_file).read(return_type='dict_reader')
                    for item in csv_reader:
                        if strategy_type is None:
                            if mode == 'custom':
                                if item['status'] != '2':
                                    if op_station:
                                        if item['op_station'] == op_station and item['strategyType'] in list(CUSTOM_STRATEGY_TYPE_DICT.values()):
                                            trades.append(item)
                                continue
                            elif item['status'] != '2':
                                if op_station:
                                    if item['op_station'] == op_station and item['strategyType'] == COMMON_STRATEGY_TYPE:
                                        trades.append(item)
                            continue
                        elif strategy_type == 'trade':
                            if item['status'] in ('0', '5'):
                                trades.append(item)
                            continue
                        elif strategy_type == 'current_trade':
                            if item['status'] in ('0', '5') and item['ip'] == LOCAL_IP:
                                trades.append(item)
                            continue
                        elif strategy_type == 'strategy_active_deleted':
                            if item['status'] in ('0', '5'):
                                trades.append(item)
                            continue
                        elif item['status'] in ('0', '5') and item['strategyType'] == str(strategy_type):
                            trades.append(item)
                if strategy_type == 'strategy_active_deleted' and len(trades) > 0:
                    trades = [item for item in trades if item.get('channel_type') == 'app']
                    trades_dict = {}
                    for item in trades:
                        backtest_content_id = item.get('backtestContentId')
                        if backtest_content_id:
                            trades_dict[backtest_content_id] = item
                    else:
                        trades = list(trades_dict.values())
    except BaseException:
        app_log.error(f'读取{trade_list_file!s}文件失败，错误原因：{get_traceback_message()!s}')
    return trades