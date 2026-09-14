# Source Generated with Decompyle++ (Python version)
# File: repro_03_while_try_except_else_for_if_continue.cpython-311.pyc (Python 3.11)

def get_trade_status(trade_id, user_id=None, return_trade_info=False):
    trade_status = 'stopped'
    if user_id is not None:
        sim_trading_list_path = '/tmp/%s/trades.csv' % user_id
    else:
        sim_trading_list_path = '/tmp/trades.csv'
    count = 1
    if os.path.exists(sim_trading_list_path):
        while count <= 3:
            try:
                with Lock(sim_trading_list_path, 'shared'):
                    reader = get_reader(sim_trading_list_path)
                for items in reader:
                    if len(items) > 0:
                        if items[0] == trade_id:
                            if return_trade_info:
                                return items
                            else:
                                return items[2]
                        continue
                    print('empty')
                    continue
            except BaseException:
                print('retry %d' % count)
                count += 1
                time.sleep(1)
            else:
                break
        else:
            if return_trade_info:
                return ['', '', trade_status]
            else:
                return trade_status
        if return_trade_info:
            return None
        return None
    else:
        print('file not found: %s' % sim_trading_list_path)
