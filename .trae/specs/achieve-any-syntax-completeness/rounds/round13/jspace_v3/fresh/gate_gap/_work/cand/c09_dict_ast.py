def _host():
    pass

def outer():
    d = {'a': 1, 'b': [2, 3]}
    d['c'] = d['a'] + 1
    return d
