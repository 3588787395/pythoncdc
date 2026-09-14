def f(items):
    try:
        for a in items:
            return a
        return None
    except BaseException:
        return None
