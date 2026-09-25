def f(universe, api, log):
    params = ['snapshot']
    if isinstance(universe, str):
        params.append(universe)
    elif isinstance(universe, (list, tuple)):
        for item in universe:
            params.append(item)
    else:
        log.info('bad')
        return {}
    log.debug(f'x {params[None:10]} y {len(params)} z')
    redata, flag = api(str(params))
    count = 0
    while not redata and count < 3:
        redata, flag = api(str(params))
        count += 1
    return redata
