# R57-10: order_entrust_info_handle 缺陷C隔离 — try 包双层 for, 内层含
# guard if + break; except BaseException 体为 error log。
# 预期: handler 体迁移到伪造的内层 for-else (else: log(...); return None),
# 真 except 体只剩 pass -> MISMATCH。
def order_entrust_info_handle(orders, entrust_list):
    try:
        for order in orders:
            for entrust in entrust_list:
                if str(entrust['entrust_no']) == order.entrust_no:
                    order.status = entrust['entrust_status']
                    break
    except BaseException:
        log.error('Order对象更新失败，错误信息：%s' % get_traceback_message())
