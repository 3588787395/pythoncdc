def fetch(stocks, n, api, lg):
    if not stocks:
        return []
    redata, flag = api(stocks)
    count = 0
    while not redata and count < 3:
        redata, flag = api(stocks)
        count += 1
    if redata:
        redata = redata.get('data')
    elif flag == 1:
        lg.info('bad')
    else:
        return None
    try:
        if redata:
            out = {}
            for s in stocks:
                out[s] = redata.get(s)
            return out
        return None
    except BaseException as x:
        lg.error(str(x))
        return None
