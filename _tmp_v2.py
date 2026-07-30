def f(x, y, z):
    try:
        return z
    except BaseException:
        return y
