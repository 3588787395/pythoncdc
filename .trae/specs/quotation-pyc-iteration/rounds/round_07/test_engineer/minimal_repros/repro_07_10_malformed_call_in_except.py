"""Repro 07-10: D10 (P2) malformed call argument in except handler.

In `api_get_financial` the HTTPError handler calls
`system_log(request_times <= 2 if e2.code == 401 else e2.code == 599)`
(quotation.pyc line 163). The conditional argument expression is
malformed: it should be a conditional call (`if e2.code == 401: ...`)
but is reduced to a single `system_log(...)` call whose argument is
a nested ternary of `==` comparisons.

Expected defect:
    system_log(request_times <= 2 if e2.code == 401 else e2.code == 599)
instead of:
    if e2.code == 401:
        system_log(request_times <= 2)
    elif e2.code == 599:
        system_log(request_times <= 2)
"""


def api_get_financial(url, request_times=0):
    try:
        response = do_request(url)
        return_data = response.json()
    except HTTPError as e2:
        if e2.code == 401:
            system_log(request_times <= 2)
        elif e2.code == 599:
            system_log(request_times <= 2)
        if 400 <= e2.code <= 499:
            return ({'error_no': e2.code, 'error_info': ''}, {})
    return ({'error_no': 0, 'error_info': ''}, return_data)
