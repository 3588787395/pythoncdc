def f(items, bad_set):
    try:
        for item in items:
            if item in bad_set:
                continue
            val = process(item)
            if val < 0:
                continue
            return {'val': val}
        return {'val': None}
        return None
    except BaseException:
        return {'val': None, 'err': True}

def process(x):
    return x
