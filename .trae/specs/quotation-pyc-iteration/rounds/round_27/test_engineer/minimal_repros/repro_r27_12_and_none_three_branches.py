def f(a, b, c):
    if a is not None and b is None:
        return 1
    elif a is None and c is not None:
        return 2
    elif b is not None and c is None:
        return 3
    return 0
