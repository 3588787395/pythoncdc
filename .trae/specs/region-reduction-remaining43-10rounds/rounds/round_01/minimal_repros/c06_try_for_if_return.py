def f(items):
    try:
        for a in items:
            if a:
                return a
    except BaseException:
        return None
