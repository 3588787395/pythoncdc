def get_trade_list_pattern(csv_reader, trade_id):
    trades = []
    for item in csv_reader:
        if item['status'] == '0':
            trades.append(item)
            break
    else:
        trades = []
    return trades
