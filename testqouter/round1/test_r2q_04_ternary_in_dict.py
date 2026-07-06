def test(fields):
    params = {'key': 'value'}
    params['fields'] = fields if fields is not None else 'default'
    return params
