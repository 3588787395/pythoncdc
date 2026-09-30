# -*- coding: utf-8 -*-
# R76-D2 复现（对照 Quote.get_individual_data）：`if redata:` 臂 =
# 赋值 + 终结核 try/except（体与 handler 全 return），其后 elif 链 +
# return None。原始 pyc 中 elif 链物理位置在 try 之前（编译器冷布局）。
def f(stocks, redata, flag):
    if stocks:
        count = 0
        while not redata and count < 3:
            sleep(1)
            redata, flag = api(stocks)
            count += 1
        if redata:
            redata = redata.get('data').get('tick')
            try:
                if redata:
                    data = {}
                    for stock in stocks:
                        data[stock] = redata.get(stock)
                    returnPa = Panel(data)
                    return returnPa
                log('data empty')
                return None
            except BaseException as x:
                log('process error: ' + str(x))
                return None
        elif flag == 1:
            log('convert error, return None')
        elif flag == -1:
            log('empty response')
        return None
    return None
