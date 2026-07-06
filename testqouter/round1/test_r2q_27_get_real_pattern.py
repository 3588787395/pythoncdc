def test(en_prod_code, fields=None):
    url = '%s/real' % 'http://api'
    params = {'en_prod_code': en_prod_code}
    if fields:
        params['fields'] = fields
    return params
