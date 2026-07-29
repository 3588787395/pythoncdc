def f(a, b, params):
    if a is not None and b is None:
        params['x'] = a
    elif a is None and b is not None:
        params['y'] = b
    elif a is not None and b is not None:
        params['x'] = a
        params['y'] = b
