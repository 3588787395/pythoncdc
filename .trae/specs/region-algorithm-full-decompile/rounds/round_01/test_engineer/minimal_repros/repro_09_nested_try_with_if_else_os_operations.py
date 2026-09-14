def kill_trade_process(user_id, trade_id, time_wait=True):
    if time_wait:
        time.sleep(1)
    if len(trade_id) != 36:
        return None
    else:
        qry_info = os.popen('ps -ef | grep %s' % trade_id).readlines()
        if len(qry_info) != 0:
            user_info = os.popen('ps -ef | grep %s' % user_id).read()
            trade_id_list = re.findall('result/(.*)/start', user_info)
            if trade_id in trade_id_list:
                trade_id_list.remove(trade_id)
            sim_path = '/tmp/%s/trades.csv' % user_id
            try:
                with Lock(sim_path):
                    os.system('kill %s' % trade_id)
            except BaseException:
                os.system('kill %s' % trade_id)
                os.system('rm -rf %s' % sim_path)
                if os.path.getsize(sim_path) == 0 and len(trade_id_list) > 0:
                    current_time = datetime.now()
                    start_time = '%s %s' % (current_time.strftime('%Y-%m-%d'), current_time.strftime('%H:%M:%S'))
                    write_info = ['header']
                    for running_id in trade_id_list:
                        write_info.append([running_id, start_time, '0'])
                        continue
                    with Lock(sim_path):
                        write(sim_path, write_info)
            lock_path = sim_path + '.lock'
            if os.path.exists(lock_path):
                try:
                    os.chmod(lock_path, 755)
                    process_id = None
                    count = 0
                    while count < 3:
                        process_id = open(lock_path).readline()
                        if process_id != '':
                            break
                        time.sleep(0.001)
                        count += 1
                except BaseException:
                    process_id = None
                if process_id is not None:
                    process_id = process_id.strip()
                    if process_id in qry_info:
                        try:
                            os.unlink(lock_path)
                        except BaseException:
                            return None
                    elif process_id == '':
                        try:
                            os.unlink(lock_path)
                        except BaseException:
                            return None
                    else:
                        return None
                return None
