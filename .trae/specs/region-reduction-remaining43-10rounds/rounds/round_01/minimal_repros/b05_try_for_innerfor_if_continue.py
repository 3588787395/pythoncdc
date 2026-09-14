def f(items):
    try:
        for a in items:
            for b in a:
                if b == 0:
                    continue
            return a
        return None
    except BaseException:
        return None
