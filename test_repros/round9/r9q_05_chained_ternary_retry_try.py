def fetch(stocks, n, api, lg):
    if stocks:
        count = int(n) if 0 < int(n) <= 200 else 200
        redata, flag = api(stocks)
        tries = 0
        while not redata and tries < 3:
            if flag == 1:
                lg.info('retry')
            elif flag == -1:
                lg.info('empty')
            redata, flag = api(stocks)
            tries += 1
        if redata:
            redata = redata.get('data')
        elif flag == 1:
            lg.info('bad')
        else:
            return None
        try:
            if redata:
                return build(redata)
            return None
        except BaseException as x:
            lg.error(str(x))
            return None
