def f(x, y, z):
    if x == 1:
        y = 10
    elif x == 2:
        y = 20
    elif x == 3:
        y = 30
    elif x == 4:
        if z:
            return z
        return y
    if y is None:
        return 0
    return y
