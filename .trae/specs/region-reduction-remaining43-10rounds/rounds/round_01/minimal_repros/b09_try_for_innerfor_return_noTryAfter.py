def f(items):
    try:
        for a in items:
            for b in a:
                pass
            return a
    except BaseException:
        return None
