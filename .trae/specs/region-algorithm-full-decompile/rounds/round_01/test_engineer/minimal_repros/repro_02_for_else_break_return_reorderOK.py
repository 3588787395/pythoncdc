# Source Generated with Decompyle++ (Python version)
# File: repro_02_for_else_break_return_reorder.cpython-311.pyc (Python 3.11)

def query_trade_strategy_info(user_id, strategy_id):
    trade_status = ['running', 'pre_restart']
    sim_trading_list_path = '/tmp/%s/trades.csv' % user_id
    if os.path.exists(sim_trading_list_path):
        try:
            with Lock(sim_trading_list_path, 'shared'):
                reader = get_reader(sim_trading_list_path)
            for items in reader:
                if len(items) > 0 and items[2] in trade_status and items[7] == strategy_id:
                    if items[16] == 'app':
                        break
                    continue
            return True
        except BaseException:
            print('error')
        return None
