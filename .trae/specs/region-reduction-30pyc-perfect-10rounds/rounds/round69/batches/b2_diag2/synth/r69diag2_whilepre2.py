def g(api, log):
    log.debug('plain entry log')
    redata, flag = api()
    count = 0
    while not redata and count < 3:
        redata, flag = api()
        count += 1
    return redata
