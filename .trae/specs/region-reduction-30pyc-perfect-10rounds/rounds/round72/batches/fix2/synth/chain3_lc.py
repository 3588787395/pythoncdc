def f(x, orders):
    if x is None:
        return [o for o in orders]
    elif isinstance(x, int):
        return [o for o in orders if o == x]
    elif isinstance(x, str):
        return [o for o in orders if o == x]
    else:
        return []
