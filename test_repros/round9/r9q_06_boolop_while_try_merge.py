def real(stocks, flag, lg, api):
    count = 0
    redata = None
    while not redata and count < 3:
        if flag == 1:
            lg.info('retry ' + str(count))
        elif flag == -1:
            lg.info('empty ' + str(count))
        redata, flag = api(stocks)
        count += 1
    if redata:
        redata = redata.get('data').get('snapshot')
    elif flag == 1:
        lg.info('bad')
    else:
        return None, flag
    try:
        if redata:
            return build(redata), 0
        lg.warn('empty')
        return None, -1
    except BaseException as x:
        lg.error(str(x))
        return None, 2
