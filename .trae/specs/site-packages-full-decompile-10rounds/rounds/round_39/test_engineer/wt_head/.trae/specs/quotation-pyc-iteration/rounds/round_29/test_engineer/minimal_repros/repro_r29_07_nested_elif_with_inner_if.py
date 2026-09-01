def f(a, b, c):
    if a:
        if b == 0:
            c = 1
        elif b == 1:
            if c > 0:
                return 1
            else:
                return 2
        if c is None:
            return 0
    return c
