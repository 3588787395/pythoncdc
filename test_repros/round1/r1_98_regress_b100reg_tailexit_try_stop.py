def f98(path, log):
    if path:
        try:
            data = path + 1
        except BaseException:
            log('e')
            return None
        log('after')
        return data
    else:
        log('no')
        return None
