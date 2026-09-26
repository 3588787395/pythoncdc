# F-THENOVER (get_trend / quotation cf2): trailing sibling if absorbed into previous
# if-body that ends with a for-loop. orig: outer if false-target = inner if test.
def get_trend(prod_code, fields=None, date=None):
    url = '%s/trend' % prod_code
    params = {'prod_code': prod_code}
    if fields:
        fields = fields.split(',')
        temp = []
        for item in fields:
            temp.append(len(item))
        params['fields'] = ','.join(temp)
    if date:
        params['date'] = date
    return url, params
