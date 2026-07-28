# Source Generated with Decompyle++ (Python version)
# File: repro_r27_ctx_02_after_code.pyc (Python 3.11)

def f(start_year, end_year, params):
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
