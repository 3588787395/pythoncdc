def f(items, bad):
    try:
        for item in items:
            if item < bad:
                continue
            return {'r': item}
        return {'r': None}
        return None
    except BaseException:
        return {'r': -1}
