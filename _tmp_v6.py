def f(x, y, z, d):
    try:
        if x is None:
            return z
    except BaseException:
        return d
    return y
