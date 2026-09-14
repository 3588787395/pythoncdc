# Source Generated with Decompyle++ (Python version)
# File: repro_04_try_except_else_nested_in_if_try_except.cpython-311.pyc (Python 3.11)

def get_trade_list(user_id, path, delete_path, mode=None):
    trades = []
    try:
        if mode == 'active' and os.path.exists(delete_path):
            try:
                with Lock(delete_path, 'shared'):
                    delete_reader = get_reader(delete_path)
                for item in delete_reader:
                    if item['status'] == '2':
                        trades.append(item)
                if os.path.exists(path):
                    with Lock(path, 'shared'):
                        reader = get_reader(path)
                    for item in reader:
                        if mode is None:
                            if item['status'] != '2':
                                trades.append(item)
                            continue
                        elif mode == 'trade':
                            if item['status'] in ('0', '5'):
                                trades.append(item)
                            continue
                        elif mode == 'active' and item['status'] in ('0', '5'):
                            trades.append(item)
            except BaseException:
                print('error1')
    except BaseException:
        print('error2')
    return trades
