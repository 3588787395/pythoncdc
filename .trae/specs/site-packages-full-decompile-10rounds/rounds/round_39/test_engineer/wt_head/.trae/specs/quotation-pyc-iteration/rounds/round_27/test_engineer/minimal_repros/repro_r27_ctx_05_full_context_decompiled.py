# Source Generated with Decompyle++ (Python version)
# File: repro_r27_ctx_05_full_context.pyc (Python 3.11)

def f(security, start_year=None, end_year=None, fields=None):
    return_data = {}
    return_data['data'] = []
    params = {'page_no': '1'}
    security = str(security)
    if start_year is not None:
        if end_year is None:
            params['start_year'] = start_year
        elif start_year is None:
            if end_year is not None:
                params['end_year'] = end_year
            elif start_year is not None and end_year is not None:
                params['start_year'] = start_year
                params['end_year'] = end_year
        elif start_year is not None and end_year is not None:
            pass
    elif start_year is None:
        pass
    elif start_year is not None and end_year is not None:
        pass
    max_stocks_num = 400
    return params
