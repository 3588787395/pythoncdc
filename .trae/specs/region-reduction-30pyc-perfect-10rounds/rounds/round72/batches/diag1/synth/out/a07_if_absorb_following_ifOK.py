# Source Generated with Decompyle++ (Python version)
# File: a07_if_absorb_following_if.pyc (Python 3.11)

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
    return (url, params)
