"""repro_01: 循环尾部 STORE_ATTR 兄弟语句 — 核心模式。

测试 aspect: 外层 for 循环体内含一个内层 while 循环。内层 while 退出后、外层 for
回边 (JUMP_BACKWARD) 之前，存在一条 STORE_ATTR 兄弟赋值语句 (data.index = time_index)。
反编译器需将该 STORE_ATTR 语句纳入外层 for 循环体生成，不可丢失。

本 repro 对应 get_str_data 残留 -3 的核心缺陷：
    for stock in stocks:
        while cond:
            ...
        data.index = time_index   # STORE_ATTR，内层循环退出后的兄弟语句
"""


class Data:
    def __init__(self):
        self.index = None


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
