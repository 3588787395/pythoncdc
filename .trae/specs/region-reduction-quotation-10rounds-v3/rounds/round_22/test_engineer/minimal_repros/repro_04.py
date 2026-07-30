"""repro_04: 内层 for 循环退出后的循环尾部 STORE_ATTR 兄弟语句。

测试 aspect: 变体——内层循环为 for（而非 while）。内层 for 退出后、外层 for 回边前，
存在 STORE_ATTR 兄弟赋值。反编译器对内层 for 与内层 while 的循环尾部块收集应一致，
不因内层循环类型不同而丢失兄弟语句。

    for stock in stocks:
        for item in stock:
            ...
        data.index = time_index   # STORE_ATTR，内层 for 退出后的兄弟语句
"""


class Data:
    def __init__(self):
        self.index = None
        self.total = 0


def f(stocks, time_index):
    order_data = {}
    for stock in stocks:
        data = Data()
        for item in stock:
            data.total += item
        data.index = time_index
        order_data[stock] = data
    return order_data
