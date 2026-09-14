def f(records, filter_val):
    try:
        for rec in records:
            if rec.get('type') == filter_val:
                continue
            if rec.get('type') == 'skip':
                continue
            return {'ok': True, 'rec': rec}
        return {'ok': False}
        return None
    except BaseException:
        return {'ok': False, 'err': 'fail'}
