# R5 minimal repro: except handler 内 Call(ternary) 语句整条丢失 + return 关键字丢失 (新发现)
# 关联缺陷：quotation.pyc api_get_financial line 163  system_log(t if e.code==401 else e.code==599) 语句丢失
# 触发区域：TRY / _generate_handler_body_statements + _generate_ternary (Call 包装的 ternary 参数语句被整体丢弃)
# 预期：except HTTPError as e2: log(t if e2.code==401 else e2.code==599); error_no = e2.code; return ({...}, None)
# R5 实际产物：
#   except HTTPError as e2:
#       error_no = e2.code
#       ({'error_no': error_no}, None)            <- log(ternary) 整条丢失 + return 关键字丢失


def handler(url, params, request_times=0):
    try:
        response = get(url, params)
        return response.json()
    except HTTPError as e2:
        log(request_times <= 2 if e2.code == 401 else e2.code == 599)
        error_no = e2.code
        return ({'error_no': error_no}, None)
    return None
