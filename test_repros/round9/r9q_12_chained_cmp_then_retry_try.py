def chained_cmp_guard(stocks, api, lg):
    data_count = int(50) if 0 < int(50) <= 200 else 200
    param = [stocks, str(data_count)]
    redata, flag = api(param)
    count = 0
    while not redata and count < 3:
        redata, flag = api(param)
        count += 1
    if redata:
        redata = redata.get('data')
    elif flag == 1:
        lg.info('bad')
    elif flag == -1:
        lg.info('none')
    else:
        return None
    try:
        if redata:
            return redata
        return None
    except BaseException as x:
        lg.error(str(x))
        return None
