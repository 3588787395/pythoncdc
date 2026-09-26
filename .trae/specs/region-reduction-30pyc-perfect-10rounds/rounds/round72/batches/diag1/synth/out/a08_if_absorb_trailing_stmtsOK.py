# Source Generated with Decompyle++ (Python version)
# File: a08_if_absorb_trailing_stmts.pyc (Python 3.11)

def filter_abnormal(stocks, standard_index):
    print('reload:')
    abnormal = []
    data = {}
    if isinstance(stocks, list):
        for stock in stocks:
            klines = len(stock)
            if klines == standard_index:
                data[stock] = klines
                continue
            abnormal.append(stock)
            continue
        print('ERROR list:%s' % abnormal)
        print('ERROR len:%s' % len(abnormal))
    panel = {'data': data, 'abnormal': abnormal}
    if len(abnormal) != 0:
        panel['tz'] = 'Asia/Shanghai'
    return panel
