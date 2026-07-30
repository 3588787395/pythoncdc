"""repro_02: 循环尾部 STORE_ATTR + STORE_SUBSCR 兄弟语句序列。

测试 aspect: 内层 while 循环退出后、外层 for 回边前，存在两条兄弟语句：
1. STORE_ATTR 赋值 (data.index = time_index)
2. STORE_SUBSCR 赋值 (order_data[stock] = data)
反编译器需保证两条语句均纳入外层循环体，且 STORE_ATTR 不被 STORE_SUBSCR 的
消费模式建模吸收/丢弃。get_str_data 实际形态：STORE_ATTR 在 STORE_SUBSCR 之前。

    for stock in stocks:
        while cond:
            ...
        data.index = time_index        # STORE_ATTR  ← 易丢失
        order_data[stock] = data       # STORE_SUBSCR ← 已生成
"""


class Data:
    def __init__(self):
        self.index = None
        self.value = 0


def f(stocks, time_index):
    order_data = {}
    for stock in stocks:
        data = Data()
        i = 0
        while i < len(stock):
            data.value = stock[i]
            i += 1
        data.index = time_index
        order_data[stock] = data
    return order_data
