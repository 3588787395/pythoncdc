# Source Generated with Decompyle++ (Python version)
# File: repro_11_truncated_function_body_with_no_as.cpython-311.pyc (Python 3.11)

def add_trade(user_id, trade_name, strategy_id):
    trade_list_file = '/tmp/%s/trades.csv' % user_id
    try:
        write_info = []
        new_file_flag = False
        if not os.path.exists(trade_list_file):
            new_file_flag = True
            write_info.append('header')
        logger = Logger(user_id, trade_name)
        logger.write('start')
        now_time = datetime.now().strftime('%H:%M:%S')
        start_time = f"{datetime.now().strftime('%Y-%m-%d')!s} {now_time!s}"
        if isinstance(trade_name, list):
            trade_name_list = trade_name
        else:
            trade_name_list = [trade_name]
        for name in trade_name_list:
            write_info.append([name, start_time])
        if len(write_info) > 0:
            with Lock(trade_list_file):
                write(trade_list_file, write_info)
            return True
        else:
            return False
    except BaseException:
        print('error')
        return None
