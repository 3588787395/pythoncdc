def f(container, item):
    if item is None:
        raise ValueError("no item")
    if container:
        if len(container) >= 2 and item not in container:
            raise KeyError("missing")
    return 0
