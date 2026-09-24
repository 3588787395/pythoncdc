# R57-03: 探针 — 同 R57-01 形状, 但尾随 return 带非 None 值 (return error_dict)。
# merge 块为 LOAD_FAST+RETURN_VALUE, 非 None-return 块,
# 预期不会被当作隐式尾声消费 -> MATCH。
def cancel_order_ex_handle(account, order):
    error_dict = account.withdraw(order)
    if error_dict.get('error_no') != 0:
        log.error('调用撤单请求失败，error_info：%s' % error_dict.get('error_info'))
    else:
        log.info('后端服务 发起撤单')
    return error_dict
