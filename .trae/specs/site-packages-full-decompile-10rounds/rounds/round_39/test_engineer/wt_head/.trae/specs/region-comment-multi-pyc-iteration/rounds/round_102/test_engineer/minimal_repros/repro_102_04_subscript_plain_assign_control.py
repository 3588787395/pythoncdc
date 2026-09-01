"""R102-04 control: plain assignment to subscript (non-augmented).

R102-03 的控制组: 普通下标赋值应保持健康。
"""


def fill(orders, frozen):
    for order in orders:
        if order.unfilled_amount <= 0:
            continue
        frozen[order.symbol] = order.unfilled_amount
    return frozen
