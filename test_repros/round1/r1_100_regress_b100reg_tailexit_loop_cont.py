def f100(items, code, log):
    for it in items:
        if code == 0:
            log('a')
        else:
            log('b')
            continue
        if code == 1:
            log('c')
        log('tail')
    return None
