"""Repro 07-09: D9 (P1, NEW) spurious `return None` after restored return.

In `api_get_financial` the HTTPError handler emits a real
`return ({...}, {})` followed by one or more spurious `return None`
statements (quotation.pyc lines 180-183). The as-var cleanup block
(`STORE_FAST e2 / DELETE_FAST e2 / RETURN_VALUE` returning None) is
not suppressed after the genuine return is restored, so each cleanup
block re-emits as `return None`.

Expected defect:
    return ({'error_no': error_no, 'error_info': error_info}, {})
    return None            # <- spurious
    return None            # <- spurious
    return None            # <- spurious
"""


def api_get_financial(url, request_times=0):
    try:
        response = do_request(url)
        return_data = response.json()
    except ConnectionRefusedError as e1:
        system_log.error(get_traceback_message())
        error_no = -1
        error_info = e1
        return ({'error_no': error_no, 'error_info': error_info}, {})
    except HTTPError as e2:
        if 400 <= e2.code <= 499:
            error_no = e2.code
            return ({'error_no': error_no, 'error_info': ''}, {})
        error_no = e2.code
        if not e2.response:
            error_info = None
        try:
            error_info = json.loads(e2.response.body.decode('utf8', 'replace'))
        except ValueError:
            error_info = str(e2.response.body.decode('utf8', 'replace'))
        return ({'error_no': error_no, 'error_info': error_info}, {})
    return ({'error_no': 0, 'error_info': ''}, return_data)
