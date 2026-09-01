# Source Generated with Decompyle++ (Python version)
# File: repro_r28_13_with_preamble.pyc (Python 3.11)

def f(security, start_year, end_year, params):
    x = eval(security)
    if start_year is not None and end_year is None:
        params['start_year'] = start_year
        return None
    elif start_year is None and end_year is not None:
        params['end_year'] = end_year
        return None
    elif start_year is not None and end_year is not None:
        params['start_year'] = start_year
        params['end_year'] = end_year
        return None
