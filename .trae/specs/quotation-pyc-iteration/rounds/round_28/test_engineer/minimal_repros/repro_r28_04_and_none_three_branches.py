def f(a, b, c, params):
    if a is not None and b is None:
        params['a'] = a
    elif a is None and c is not None:
        params['c'] = c
    elif b is not None and c is None:
        params['b'] = b
