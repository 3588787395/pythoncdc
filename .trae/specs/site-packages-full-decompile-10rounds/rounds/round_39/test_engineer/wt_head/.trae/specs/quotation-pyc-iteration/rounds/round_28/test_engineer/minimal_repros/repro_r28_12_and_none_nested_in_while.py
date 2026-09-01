def f(a, b):
    while True:
        if a is not None and b is None:
            return 1
        elif a is None and b is not None:
            return 2
        break
    return 0
