"""Repro: Chained compare inside except handler becomes bare number if."""


def api_get_financial(url, request_times=0):
    try:
        response = do_request(url)
        return_data = response.json()
    except HTTPError as e2:
        system_log.error(get_traceback_message())
        if 400 <= e2.code <= 499:
            error_no = e2.code
            return ({'error_no': error_no, 'error_info': ''}, {})
    return ({'error_no': 0, 'error_info': ''}, return_data)
