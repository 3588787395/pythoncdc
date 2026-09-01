def func(x):
    if not isinstance(x, int):
        raise TypeError("not int")
    return x
