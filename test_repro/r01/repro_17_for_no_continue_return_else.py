def f(items, bad):
    try:
        for item in items:
            if item == bad:
                pass
            result = item + 1
            return {'status': 'ok', 'data': result}
        return {'status': 'empty'}
        return None
    except BaseException:
        return {'status': 'error'}
