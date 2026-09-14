def f(items, blacklist):
    try:
        for item in items:
            if item in blacklist:
                continue
            result = process(item)
            return {'status': 'ok', 'data': result}
        return {'status': 'empty'}
        return None
    except BaseException:
        return {'status': 'error'}

def process(x):
    return x * 2
