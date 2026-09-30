# Source Generated with Decompyle++ (Python version)
# File: r76_07_terminal_try_elif_dec.pyc (Python 3.11)

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
                else:
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
    else:
        return None
