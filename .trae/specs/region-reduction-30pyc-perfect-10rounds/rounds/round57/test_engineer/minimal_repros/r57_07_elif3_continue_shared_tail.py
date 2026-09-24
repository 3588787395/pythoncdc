# R57-07: order_entrust_info_handle 缺陷A隔离 — 双层循环内 if/elif/else 链,
# else 臂 continue 退出循环, 其余臂 JUMP_FORWARD 汇入链后公共尾语句。
# 预期: 公共尾被内联进首个非 else 臂, 其余臂丢失尾 -> MISMATCH。
def order_entrust_info_handle(orders, entrust_list):
    for order in orders:
        for entrust in entrust_list:
            if str(entrust['entrust_no']) == order.entrust_no:
                if order.type == 'stock':
                    stock_code = entrust.get('stock_code') + '.SS'
                elif order.type == 'future':
                    stock_code = entrust.get('contract_code') + '.FF'
                else:
                    log.error('不识别的业务类型：%s' % order.type)
                    continue
                order.code = stock_code
                order.seen = True
