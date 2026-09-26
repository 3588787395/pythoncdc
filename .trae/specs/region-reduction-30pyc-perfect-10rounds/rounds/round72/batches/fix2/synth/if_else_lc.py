def f(x, orders):
    if x is None:
        return [o for o in orders]
    else:
        return [o for o in orders if o == x]
