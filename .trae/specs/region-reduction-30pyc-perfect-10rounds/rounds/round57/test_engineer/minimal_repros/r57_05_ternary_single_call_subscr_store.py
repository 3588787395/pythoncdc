# R57-05: 探针 — R57-04 去掉外层 int(), 仅一层 float(T) 调用。
# 用于定位 merge 消费者链在第几层调用处断裂。
def get_entrust_item_info(order):
    out = {}
    item = order.raw
    out['entrust_no'] = str(item.get('entrust_no'))
    out['amount'] = float('+%s' % item.get('entrust_amount') if item.get('entrust_bs') == '1' else '-%s' % item.get('entrust_amount'))
    return out
