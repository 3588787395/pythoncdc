# Source Generated with Decompyle++ (Python version)
# File: repro_08_with_in_try_if_continue_dead_code.cpython-311.pyc (Python 3.11)

def trade_operation(user_id, trade_id, operation):
    trade_list_file = '/tmp/%s/trades.csv' % user_id
    delete_file = '/tmp/%s/deleted.csv' % user_id
    if isinstance(trade_id, str):
        trade_id_list = [trade_id]
    elif isinstance(trade_id, list):
        trade_id_list = trade_id
    else:
        return False
    try:
        if os.path.exists(trade_list_file):
            with Lock(trade_list_file):
                reader = get_reader(trade_list_file)
                write_info = []
                delete_info = []
                new_file_flag = False
                if not os.path.exists(delete_file):
                    new_file_flag = True
                    delete_info.append('header')
                for items in reader:
                    if items[0] in trade_id_list:
                        if operation == 'start':
                            items[2] = '0'
                            operation = 'restart'
                        if operation == 'stop':
                            items[2] = '1'
                        if operation == 'delete':
                            items[2] = '2'
                            delete_info.append(items)
                            continue
                        elif operation == 'pause':
                            items[2] = '3'
                        if operation == 'reload':
                            items[2] = '4'
                    write_info.append(items)
                    continue
                if len(write_info) > 0:
                    write(trade_list_file, write_info)
                    if len(delete_info) > 0:
                        mode = 'w' if new_file_flag else 'a'
                        Lock(delete_file)
                        write(delete_file, delete_info)
                        return True
                    else:
                        return False
                else:
                    with Lock(delete_file):
                        pass
                with Lock(delete_file):
                    pass
        else:
            return False
    except BaseException:
        return False
