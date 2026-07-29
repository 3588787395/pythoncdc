def f(a, b, params):
    if a is not None:
        if b is not None:
            params['x'] = 1
        else:
            params['x'] = 2
    else:
        if b is not None:
            params['x'] = 3
        else:
            params['x'] = 4
