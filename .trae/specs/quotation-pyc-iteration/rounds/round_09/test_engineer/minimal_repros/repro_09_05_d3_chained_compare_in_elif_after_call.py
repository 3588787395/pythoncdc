"""Repro 09-05: D3 variant — chained compare preceded by if/elif in except.

The quotation.pyc::api_get_financial except handler has the structure:
    except HTTPError as e2:
        system_log.error(get_traceback_message())   # call
        if e2.code == 401:                          # if
            ...
        elif e2.code == 599:                        # elif
            ...
        elif 400 <= e2.code <= 499:                 # elif with chained compare
            ...
This repro isolates the if/elif-then-chained-compare tail. The D3
defect fires on the `elif 400 <= e2.code <= 499:` branch.

Expected defect: `elif 499:` (chained compare lost on the elif branch).
"""


def api_get_financial(url, request_times=0):
    try:
        response = do_request(url)
        return_data = response.json()
    except HTTPError as e2:
        system_log.error(get_traceback_message())
        if e2.code == 401:
            return retry(url, request_times)
        elif e2.code == 599:
            return retry(url)
        elif 400 <= e2.code <= 499:
            error_no = e2.code
            return ({'error_no': error_no, 'error_info': ''}, {})
        else:
            error_no = -1
            return ({'error_no': error_no, 'error_info': ''}, {})
    return ({'error_no': 0, 'error_info': ''}, return_data)
