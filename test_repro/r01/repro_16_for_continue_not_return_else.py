def f(data, skip):
    try:
        for item in data:
            if not item:
                continue
            return item
        return None
        return None
    except BaseException:
        return -1
