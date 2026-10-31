def f(items, flag):
    if flag:
        raise RuntimeError("flagged")
    if items:
        if not (len(items) >= 2 and isinstance(items[0], str)):
            raise TypeError("bad items")
    return len(items)
