# R57-17: 探针 — R57_05 的 int() 单层调用版本 (下标存储)。
# 定位 merge 消费者链断裂与外层函数名 (int/float) 是否相关。
def get_entrust_item_info(order):
    out = {}
    item = order.raw
    out['entrust_no'] = str(item.get('entrust_no'))
    out['amount'] = int('+%s' % item.get('entrust_amount') if item.get('entrust_bs') == '1' else '-%s' % item.get('entrust_amount'))
    return out
