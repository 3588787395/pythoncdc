"""Repro 08-05: D10 (P2) malformed call in except handler.

In `api_get_financial` (quotation.pyc line 158) the HTTPError handler
contains an if/elif chain:
    except HTTPError as e2:
        system_log.error(get_traceback_message())
        if e2.code == 401:
            if request_times <= 2:
                time.sleep(10)
                request_times += 1
                return api_get_financial(url, params, request_times)
        elif e2.code == 599:
            return api_get_financial(url, params)
        elif 400 <= e2.code <= 499:
            ...
The decompiler merges the `system_log.error(...)` call with the
`e2.code == 401 / e2.code == 599` if/elif conditions and emits:
    system_log(request_times <= 2 if e2.code == 401 else e2.code == 599)
The conditional call becomes a conditional argument; the .error attr
and the get_traceback_message arg are dropped.

Expected defect:
    system_log(request_times <= 2 if e2.code == 401 else e2.code == 599)
"""


def api_get_financial(url, request_times=0):
    try:
        response = do_request(url)
        return_data = response.json()
    except HTTPError as e2:
        system_log.error(get_traceback_message())
        if e2.code == 401:
            if request_times <= 2:
                time.sleep(10)
                request_times += 1
                return api_get_financial(url, params, request_times)
        elif e2.code == 599:
            return api_get_financial(url, params)
        error_no = e2.code
        return ({'error_no': error_no, 'error_info': ''}, {})
    return ({'error_no': 0, 'error_info': ''}, return_data)
