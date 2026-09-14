def f(items):
    try:
        for a in items:
            break
    except BaseException:
        return None
