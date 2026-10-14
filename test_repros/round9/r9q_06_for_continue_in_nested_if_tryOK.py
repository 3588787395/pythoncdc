# Source Generated with Decompyle++ (Python version)
# File: r9q_06_for_continue_in_nested_if_try.pyc (Python 3.11)

def real(stocks, flag, lg, api):
    redata = None
    count = 0
    while not redata and count < 3:
        if flag == 1:
            lg.info('retry')
        elif flag == -1:
            lg.info('empty')
        redata, flag = api(stocks)
        count += 1
    if redata:
        redata = redata.get('data').get('snapshot')
    elif flag == 1:
        lg.info('bad')
    elif flag == -1:
        lg.info('none')
    else:
        return (None, flag)
    try:
        if redata:
            data = {}
            for item in stocks:
                for i, v in enumerate(redata[item]):
                    if i == 0:
                        data[i] = fmt(v)
                        continue
                    data[i] = [v]
                    continue
                return (build(data), 0)
            return (data, 0)
        else:
            lg.warn('empty')
            return (None, -1)
    except BaseException as x:
        lg.error(str(x))
        return (None, 2)
