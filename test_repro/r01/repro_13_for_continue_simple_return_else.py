def f(items, skip):
    try:
        for item in items:
            if item == skip:
                continue
            return item + 1
        return -1
        return None
    except BaseException:
        return -2
