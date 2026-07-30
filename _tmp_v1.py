def f(x, y, z):
    try:
        if x is None:
            return z
    except BaseException:
        return y
