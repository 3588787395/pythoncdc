def f(x, orders):
    if x is None:
        return orders
    elif isinstance(x, int):
        return orders
    elif isinstance(x, str):
        return orders
    else:
        return None
