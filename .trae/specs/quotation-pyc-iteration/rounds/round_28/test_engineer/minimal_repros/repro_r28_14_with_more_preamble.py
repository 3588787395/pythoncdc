def f(security, start_year, end_year, params):
    return_data = {}
    return_data['data'] = []
    url = '%s/info' % 'x'
    params = {'page_no': '1'}
    security = eval(security)
    if start_year is not None and end_year is None:
        params['start_year'] = start_year
    elif start_year is None and end_year is not None:
        params['end_year'] = end_year
    elif start_year is not None and end_year is not None:
        params['start_year'] = start_year
        params['end_year'] = end_year
