# R57-14 (负对照): try 包单层 for (无 break、无嵌套循环) + except 体。
# 预期不触发 for-else 伪造 -> MATCH。
def order_entrust_info_handle(orders):
    try:
        for order in orders:
            order.done = True
    except BaseException:
        log.error('Order对象更新失败，错误信息：%s' % get_traceback_message())
