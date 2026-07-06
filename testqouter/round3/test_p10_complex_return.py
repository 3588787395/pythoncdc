def test(x, y):
    if x is None:
        return y
    if not isinstance(x, int):
        return -1
    return x + y
