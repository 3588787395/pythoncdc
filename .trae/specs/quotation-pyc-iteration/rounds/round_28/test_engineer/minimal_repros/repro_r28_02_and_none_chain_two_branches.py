def f(a, b, params):
    if a is not None and b is None:
        params['a'] = a
    elif a is None and b is not None:
        params['b'] = b
