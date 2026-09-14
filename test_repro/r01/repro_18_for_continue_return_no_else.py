def f(items, bad):
    try:
        for item in items:
            if item == bad:
                continue
            result = item + 1
            return {'status': 'ok', 'data': result}
    except BaseException:
        return {'status': 'error'}
    return {'status': 'empty'}
