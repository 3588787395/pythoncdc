def trade_count(trade_list_file):
    count = 0
    try:
        if os.path.exists(trade_list_file):
            with Lock(trade_list_file, 'shared'):
                reader = get_reader(trade_list_file)
            for line in reader:
                if line[2] == '0' or line[2] == '3':
                    count += 1
                if count >= 10:
                    break
                continue
        else:
            print('file not found')
        return count
        return None
    except BaseException:
        print('error')
        return count
