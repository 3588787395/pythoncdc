def f(data, key):
    if key is None:
        raise ValueError("no key")
    if len(data) >= 2:
        if not (isinstance(data[0], str) and isinstance(data[1], str)):
            raise TypeError("bad pair")
    return sum(data)
