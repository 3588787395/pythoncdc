# R57-09: order_entrust_info_handle 缺陷B隔离 — 尾随 break 中转块
# (POP_TOP + JUMP_FORWARD) 有两个前驱: if 真臂 fall-through + 假臂 POP_JUMP。
# R55-A 合取⑦(唯一前驱)不满足, 预期被误发为 else: break, 语义反转 -> MISMATCH。
def order_entrust_info_handle(orders, entrust):
    for order in orders:
        entrust_status = str(entrust['entrust_status'])
        if entrust_status in ('4', '5', '7', '8'):
            order._filled_amount = float(entrust['business_amount'])
        break
