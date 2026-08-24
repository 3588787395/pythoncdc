"""R102-03: augmented assignment to subscript inside for loop.

stock_account.update_account 同型:
  frozen_amount[order.symbol] += order.unfilled_amount
疑似被降级为普通赋值 (丢 COPY/COPY/SWAP 增广序列)。
"""


def drain(orders, frozen):
    for order in orders:
        if order.unfilled_amount <= 0:
            continue
        if order.symbol not in frozen:
            frozen[order.symbol] = 0
        frozen[order.symbol] += order.unfilled_amount
        order.unfilled_amount = 0
    return frozen
