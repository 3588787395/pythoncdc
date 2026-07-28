def f(a, b, params):
    if a is None:
        if b is None:
            params['x'] = 1
        else:
            params['x'] = 2
    else:
        if b is None:
            params['x'] = 3
        else:
            params['x'] = 4
