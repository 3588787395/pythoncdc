def f(x, y, z, d):
    try:
        if x is None or y is None:
            return z
    except BaseException:
        return d
    return y
