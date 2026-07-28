def f(x, y, z):
    if x == 1:
        if y == 1:
            z = 10
        elif y == 2:
            z = 20
        if z is None:
            return 0
    elif x == 2:
        z = 30
    return z
