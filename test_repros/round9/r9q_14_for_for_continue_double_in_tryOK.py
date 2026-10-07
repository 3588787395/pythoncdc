# Source Generated with Decompyle++ (Python version)
# File: r9q_14_for_for_continue_double_in_try.pyc (Python 3.11)

def real(stocks, api, lg):
    redata = api()
    count = 0
    while not redata and count < 3:
        if count == 1:
            lg.info('a')
        else:
            lg.info('b')
        redata = api()
        count += 1
    if redata:
        redata = redata.get('data').get('snap')
    elif count == 1:
        lg.info('bad')
    elif count == -1:
        lg.info('none')
    else:
        return (None, count)
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
            return (None, -1)
    except BaseException as x:
        lg.error(str(x))
        return (None, 2)
