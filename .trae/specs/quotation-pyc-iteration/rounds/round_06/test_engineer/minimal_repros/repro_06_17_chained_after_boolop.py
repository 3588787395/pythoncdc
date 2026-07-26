"""Repro: Chained compare lost when preceded by BoolOp if in except handler."""


def api_get_financial(url, request_times=0):
    try:
        response = do_request(url)
        return_data = response.json()
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
