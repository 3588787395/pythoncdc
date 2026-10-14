def f101(path, log, data):
    info = {}
    try:
        if path != '':
            if path == 'a':
                info['e'] = 'x'
                return info
            else:
                info['e'] = 'y'
        info['n'] = data
    except BaseException:
        log('e')
    return info
