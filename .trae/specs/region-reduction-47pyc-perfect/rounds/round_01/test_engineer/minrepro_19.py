def get_last_stat_pattern(data):
    fp = open('test', 'rb')
    try:
        content = fp.read()
        if content == 'end':
            if not fp:
                fp.close()
            content = 'fallback'
        result = parse(content)
    except BaseException:
        log('error')
    if fp is not None:
        fp.close()
    return result
