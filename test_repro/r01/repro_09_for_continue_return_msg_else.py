def f(items, bad):
    try:
        for item in items:
            if item == bad:
                continue
            result = do_work(item)
            msg = 'success for %s' % item
            log_info(msg)
            return {'error_no': 0, 'result': result}
        return {'error_no': -1, 'info': 'all filtered'}
        return None
    except BaseException:
        return {'error_no': -1, 'info': 'error'}

def do_work(x):
    return x

def log_info(m):
    pass
