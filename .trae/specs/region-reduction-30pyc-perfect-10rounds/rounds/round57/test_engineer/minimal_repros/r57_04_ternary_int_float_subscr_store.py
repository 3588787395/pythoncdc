# R57-04: get_entrust_item_info 核心缺陷语句。
# out['amount'] = int(float(T)) — 三元 T 为嵌套调用实参, 存储目标为下标赋值。
# 预期: 三元被误绑为下标键、float 变裸值, int() 包装与真实目标 out['amount']
# 丢失 (真 pyc 中被发成 item[T] = float) -> MISMATCH。
def get_entrust_item_info(order):
    out = {}
    item = order.raw
    out['entrust_no'] = str(item.get('entrust_no'))
    out['amount'] = int(float('+%s' % item.get('entrust_amount') if item.get('entrust_bs') == '1' else '-%s' % item.get('entrust_amount')))
    return out
