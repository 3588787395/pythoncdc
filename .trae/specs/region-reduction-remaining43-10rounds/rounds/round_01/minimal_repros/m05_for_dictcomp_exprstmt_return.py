def f(items):
    for a in items:
        acc = {b: b for b in a if b}
        msg = 'ok'
        log.info(msg)
        return {'data': acc}
