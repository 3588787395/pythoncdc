def func(x, y):
    a = None
    if y:
        a = a or x.get(y)
        b = a
    return b
