def f(x, y, z, d):
    if x is None or y is None:
        return z
    elif x == 0:
        return z + 1
    return y
