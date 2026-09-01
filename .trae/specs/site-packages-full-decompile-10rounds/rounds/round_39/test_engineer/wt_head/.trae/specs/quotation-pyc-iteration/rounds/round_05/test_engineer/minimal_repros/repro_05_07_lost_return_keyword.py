# R5 minimal repro: return 关键字丢失 -> 裸 (tuple,) 表达式
# 关联缺陷：quotation.pyc api_get_financial line 161/169/179/184  ({...}, {}) 裸表达式 (新发现)
# 触发区域：TRY / _generate_handler_body_statements + _generate_return_ast (except 内 return (tuple,) 退化为裸 Expr)
# 预期：except E as e: err=-1; info=e; return ({'error_no':err,'error_info':info}, {})
# R5 实际产物：({...}, {})  (return 关键字丢失, 退化为裸 tuple 表达式)


def api_get_financial(url, params=None):
    return_data = None
    try:
        response = get(url, params)
        return_data = response.json()
    except ConnectionRefusedError as e1:
        error_no = -1
        error_info = e1
        return ({'error_no': error_no, 'error_info': error_info}, {})
    except HTTPError as e2:
        error_no = e2.code
        error_info = str(e2)
        return ({'error_no': error_no, 'error_info': error_info}, {})
    except BaseException as e3:
        error_no = -1
        error_info = e3
        return ({'error_no': error_no, 'error_info': error_info}, {})
    return ({'error_no': 0, 'error_info': ''}, return_data)
