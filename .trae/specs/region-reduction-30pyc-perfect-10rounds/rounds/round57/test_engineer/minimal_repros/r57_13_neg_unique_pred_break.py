# R57-13 (负对照): break 位于 if 真臂内, break 中转块唯一前驱 (真臂 fall-through)。
# R55-A 合取⑦满足, 预期正确消费中转块 -> MATCH。
def order_entrust_info_handle(orders, entrust):
    for order in orders:
        if str(entrust['entrust_status']) == 'done':
            order._filled_amount = float(entrust['business_amount'])
            break
