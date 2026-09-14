def check_and_update_trade_pattern(user_id_list):
    for user_id in user_id_list:
        count = 0
        while count < 3:
            try:
                items = read_data(user_id)
                write_data(items)
            except BaseException:
                if count == 2:
                    log('error')
                count += 1
                sleep(1)
