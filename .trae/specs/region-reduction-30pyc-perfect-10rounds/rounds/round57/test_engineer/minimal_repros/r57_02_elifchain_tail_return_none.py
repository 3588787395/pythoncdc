# R57-02: cancel_order_ex_handle 变体 — 尾部 if/else 之前有 if/elif/else 链,
# 链中含 in-arm return None; 末尾显式 return None 预期同样被丢弃。
def cancel_order_ex_handle(account, order):
    error_dict = account.withdraw(order)
    if order.type == 'stock':
        code = order.symbol.replace('XSHG', 'SS')
    elif order.type == 'future':
        code = order.symbol
    else:
        log.error('传入交易类型不支持：%s，撤单取消' % order.type)
        return None
    if error_dict.get('error_no') != 0:
        log.error('调用撤单请求失败，error_info：%s' % error_dict.get('error_info'))
    else:
        log.info('后端服务 操作账户股票代码：【%s】 发起撤单' % code)
    return None
