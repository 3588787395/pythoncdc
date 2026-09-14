# Source Generated with Decompyle++ (Python version)
# File: _test_trade_list_pattern.pyc (Python 3.11)

def get_trade_list_pattern(csv_reader, trade_id):
    trades = []
    for item in csv_reader:
        if item['status'] == '0':
            trades.append(item)
    else:
        trades = []
    return trades
