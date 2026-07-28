def f(a, b):
    if a is not None and b is None:
        return 1
    elif a is None and b is not None:
        return 2
    return 0
