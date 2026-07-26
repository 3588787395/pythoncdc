# R5 minimal repro: except handler 内 if e2.code == 499 Compare/块丢失 (R4 残留 #1 同源)
# 关联缺陷：quotation.pyc api_get_financial line 162-169  if 499: pass (R4 残留 #1)
# 触发区域：TRY / _generate_handler_body_statements (前驱 ternary-in-call-arg Compare 干扰后续 if 区域识别)
# 预期：log(t if e.code==401 else e.code==599); if e.code == 499: pass; else: return (tuple,)
#                                            error_no = e.code; ...; return (tuple,)
# R5 实际产物：
#   request_times <= 2 if e2.code == 401 else e2.code == 599   <- 裸 ternary (log() Call 包裹丢失)
#   error_no = e2.code
#   if not e2.response: ...           <- if e2.code==499 整块丢失 + 末尾 return 丢失


def api_get_financial(url, params=None, request_times=0):
    return_data = None
    try:
        response = get(url, params)
        return_data = response.json()
    except HTTPError as e2:
        log(request_times <= 2 if e2.code == 401 else e2.code == 599)
        if e2.code == 499:
            pass
        else:
            error_no = -1
            error_info = 'server error %d' % e2.code
            return ({'error_no': error_no, 'error_info': error_info}, {})
        error_no = e2.code
        if not e2.response:
            error_info = None
        else:
            error_info = parse(e2.response.body)
        return ({'error_no': error_no, 'error_info': error_info}, return_data)
    return ({'error_no': 0, 'error_info': ''}, return_data)
