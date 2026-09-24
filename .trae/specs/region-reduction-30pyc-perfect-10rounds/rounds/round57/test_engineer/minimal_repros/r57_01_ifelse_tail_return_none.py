# R57-01: cancel_order_ex_handle 核心缺陷 — 尾随显式 return None 被丢弃。
# orig 形状: 尾部 if/else 两分支汇入显式 `return None` 块
# (then 臂 JUMP_FORWARD 汇入, else 臂 fall-through 汇入)。
# 3.11.7 代码生成实证: 无显式 return 时 then 臂内联 LOAD_CONST None+RETURN_VALUE,
# 不会产生 JUMP_FORWARD; 故跳入 return 块的 JUMP 边是显式 return 的判定信号。
# 预期: 反编译丢失尾随 return None -> 重编译 +1 指令 -> MISMATCH [seq_len]。
def cancel_order_ex_handle(account, order):
    error_dict = account.withdraw(order)
    if order is None:
        log.error('获取委托编号失败，撤单取消')
        return None
    if error_dict.get('error_no') != 0:
        log.error('调用撤单请求失败，error_info：%s' % error_dict.get('error_info'))
    else:
        log.info('后端服务 操作账户股票代码：【%s】 委托号：【%s】 发起撤单' % (order.symbol, order.entrust_no))
    return None
