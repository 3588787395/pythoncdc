def f(items):
    try:
        for a in items:
            for b in a:
                pass
            return a
        return None
    except BaseException:
        return None
