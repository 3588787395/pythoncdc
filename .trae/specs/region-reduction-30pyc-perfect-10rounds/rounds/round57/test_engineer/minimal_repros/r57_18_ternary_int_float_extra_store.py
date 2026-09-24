# R57-18: R57-04 加一条前置同类下标赋值 (更接近真函数的栈历史)。
# 预期仍 -> MISMATCH (真 pyc 中该语句前有多条 out[...] = 赋值)。
def get_entrust_item_info(order):
    out = {}
    item = order.raw
    out['entrust_no'] = str(item.get('entrust_no'))
    out['entrust_bs'] = str(item.get('entrust_bs'))
    out['amount'] = int(float('+%s' % item.get('entrust_amount') if item.get('entrust_bs') == '1' else '-%s' % item.get('entrust_amount')))
    return out
