def f(x, orders):
    if x is None:
        return orders
    elif isinstance(x, int):
        return orders
    else:
        return [o for o in orders]
