def f(maxsize, typed):
    if isinstance(maxsize, int):
        maxsize = 0
    elif callable(maxsize):
        user_function, maxsize = maxsize, 128
        info = lambda : maxsize
        typed = 5
    return (maxsize, typed, user_function)
