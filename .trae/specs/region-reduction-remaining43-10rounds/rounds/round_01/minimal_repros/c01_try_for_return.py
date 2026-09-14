def f(items):
    try:
        for a in items:
            return a
    except BaseException:
        return None
