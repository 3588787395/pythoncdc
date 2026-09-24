# R57-16: R57-01 极简版 — 函数仅含尾部 if/else + 显式 return None,
# 无任何前置语句。预期同样 +1 -> MISMATCH。
def cancel_order_ex_handle(account, order):
    if account.error_no != 0:
        log.error('fail: %s' % account.error_info)
    else:
        log.info('ok')
    return None
