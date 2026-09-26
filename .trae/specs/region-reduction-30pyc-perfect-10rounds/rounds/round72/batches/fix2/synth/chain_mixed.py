def f(x, orders):
    if x is None:
        return orders
    elif isinstance(x, int):
        y = x
        return [o for o in orders if o == y]
    else:
        return []
