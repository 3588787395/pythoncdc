# F-THENOVER (filter_abnormal_data / load_daily cf2): statements after an if whose
# body holds a for-loop are indented into the then-branch by the decompiler.
def filter_abnormal(stocks, standard_index):
    print('reload:')
    abnormal = []
    data = {}
    if isinstance(stocks, list):
        for stock in stocks:
            klines = len(stock)
            if klines == standard_index:
                data[stock] = klines
            else:
                abnormal.append(stock)
        print('ERROR list:%s' % abnormal)
        print('ERROR len:%s' % len(abnormal))
    panel = {'data': data, 'abnormal': abnormal}
    if len(abnormal) != 0:
        panel['tz'] = 'Asia/Shanghai'
    return panel
