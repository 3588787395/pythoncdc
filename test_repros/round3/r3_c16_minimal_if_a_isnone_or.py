def f(a, x, y):
    if a:
        if x is None or y is None:
            return None
        return use(x, y)
    return None
