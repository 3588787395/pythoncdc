# R57-08: 探针 — R57-07 的两臂极简版 (无 guard if, 无 elif 链)。
# 用于定位公共尾内联缺陷是否依赖 elif 链结构。
def order_entrust_info_handle(orders, entrust_list):
    for order in orders:
        for entrust in entrust_list:
            if order.type == 'stock':
                stock_code = entrust.get('stock_code') + '.SS'
            else:
                log.error('不识别的业务类型：%s' % order.type)
                continue
            order.code = stock_code
            order.seen = True
