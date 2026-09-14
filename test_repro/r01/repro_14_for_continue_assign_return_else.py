def f(a, b):
    try:
        for x in a:
            if x == b:
                continue
            y = x * 2
            return y
        return 0
        return None
    except BaseException:
        return -1
