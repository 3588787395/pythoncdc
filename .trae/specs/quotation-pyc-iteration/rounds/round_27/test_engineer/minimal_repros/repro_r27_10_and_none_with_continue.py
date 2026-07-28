def f(items):
    for i in items:
        if i is not None and i > 0:
            continue
        return i
    return None
