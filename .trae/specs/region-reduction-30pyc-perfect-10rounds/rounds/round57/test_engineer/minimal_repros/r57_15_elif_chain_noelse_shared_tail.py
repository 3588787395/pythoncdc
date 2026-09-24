# R57-15: 探针 — R57-07 去掉 else 臂 (链无 else, 假边自然落入公共尾)。
# 用于定位公共尾缺陷是否依赖 else 臂 continue 的非对称出口。
def order_entrust_info_handle(orders, entrust_list):
    for order in orders:
        for entrust in entrust_list:
            if str(entrust['entrust_no']) == order.entrust_no:
                if order.type == 'stock':
                    stock_code = entrust.get('stock_code') + '.SS'
                elif order.type == 'future':
                    stock_code = entrust.get('contract_code') + '.FF'
                order.code = stock_code
                order.seen = True
