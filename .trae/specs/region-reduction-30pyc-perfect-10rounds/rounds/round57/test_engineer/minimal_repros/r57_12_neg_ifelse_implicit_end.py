# R57-12 (负对照): R57-01 去掉尾随显式 return None, 函数以 if/else 隐式收尾。
# 3.11.7 下 then 臂本来就会内联 LOAD_CONST None+RETURN_VALUE (无 JUMP_FORWARD),
# 预期反编译(if/else)重编译与 orig 逐指令一致 -> MATCH。
def cancel_order_ex_handle(account, order):
    error_dict = account.withdraw(order)
    if order is None:
        log.error('获取委托编号失败，撤单取消')
        return None
    if error_dict.get('error_no') != 0:
        log.error('调用撤单请求失败，error_info：%s' % error_dict.get('error_info'))
    else:
        log.info('后端服务 发起撤单')
