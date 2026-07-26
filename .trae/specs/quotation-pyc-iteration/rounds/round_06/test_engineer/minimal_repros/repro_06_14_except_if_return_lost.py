"""Repro 06-14: Lost return in if-branch inside except handler.

When an except handler contains an `if/elif` chain where each branch
returns a tuple, the return value construction (BUILD_TUPLE) and the
POP_EXCEPT + as-var cleanup + RETURN_VALUE are split across separate
basic blocks, causing `return (a, b)` to become bare `(a, b)` Expr.
"""


def fetch(url):
    try:
        response = do_request(url)
        return_data = response.json()
    except ConnectionRefusedError as e1:
        system_log.error(get_traceback_message())
        error_no = -1
        error_info = e1
        return ({'error_no': error_no, 'error_info': error_info}, {})
    except HTTPError as e2:
        system_log.error(get_traceback_message())
        if request_times <= 2 and (e2.code == 401 or e2.code == 599):
            time.sleep(10)
            request_times = request_times + 1
            return api_get_financial(url, request_times=request_times)
        if 400 <= e2.code <= 499:
            error_no = e2.code
            return ({'error_no': error_no, 'error_info': ''}, {})
    return ({'error_no': 0, 'error_info': ''}, return_data)
