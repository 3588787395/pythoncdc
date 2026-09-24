# R57-06: 探针 — R57-04 改为普通名字赋值 amount = int(float(T))。
# 用于定位缺陷是否为下标存储目标 (STORE_SUBSCR) 特有。
def get_entrust_item_info(order):
    item = order.raw
    amount = int(float('+%s' % item.get('entrust_amount') if item.get('entrust_bs') == '1' else '-%s' % item.get('entrust_amount')))
    return amount
