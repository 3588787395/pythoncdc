def f(items):
    for a in items:
        msg = 'hi %s' % a
        log.info(msg)
        return {'error_no': 0, 'error_info': '', 'index': a}
