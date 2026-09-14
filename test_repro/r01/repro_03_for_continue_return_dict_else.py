def f(servers, bad):
    try:
        for s in servers:
            if s == bad:
                continue
            info = check(s)
            return {'ok': True, 'info': info}
        return {'ok': False, 'reason': 'all bad'}
        return None
    except BaseException:
        return {'ok': False, 'reason': 'error'}

def check(s):
    return s
