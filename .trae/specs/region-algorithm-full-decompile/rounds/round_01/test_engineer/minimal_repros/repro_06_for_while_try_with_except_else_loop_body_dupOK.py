# Source Generated with Decompyle++ (Python version)
# File: repro_06_for_while_try_with_except_else_loop_body_dup.cpython-311.pyc (Python 3.11)

def check_and_update_trade(run_log, user_id_list, restart_mode=None):
    for user_id in user_id_list:
        count = 0
        while count < 3:
            try:
                trade_list_file = '/tmp/%s/trades.csv' % user_id
                with Lock(trade_list_file):
                    reader = get_reader(trade_list_file)
                    write_info = []
                    reader = get_reader(trade_list_file)
                    write_info = []
                    for items in reader:
                        if items[2] in ('0', '5'):
                            trade_id = items[0]
                            if restart_mode is None and items[15] != '127.0.0.1':
                                run_log.warning('skip')
                            else:
                                output = os.popen('grep %s' % trade_id)
                                matches = re.findall(trade_id, output.read())
                                if len(matches) == 0:
                                    items[2] = '5'
                                else:
                                    items[2] = '0'
                        write_info.append(items)
                    if len(write_info) > 0:
                        write(trade_list_file, write_info)
            except BaseException:
                if count == 2:
                    run_log.error('failed for %s' % user_id)
                count += 1
                time.sleep(1)
            else:
                break
