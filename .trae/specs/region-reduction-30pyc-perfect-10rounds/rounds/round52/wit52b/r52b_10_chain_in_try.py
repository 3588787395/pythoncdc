def w(a, b, c, x):
    try:
        if a < b < c:
            x = 2
    except ValueError:
        x = 3
    return x
