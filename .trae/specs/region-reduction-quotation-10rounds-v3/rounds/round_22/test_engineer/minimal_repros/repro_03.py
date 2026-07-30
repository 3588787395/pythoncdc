"""repro_03: 循环尾部多条 STORE_ATTR 兄弟语句。

测试 aspect: 内层循环退出后、外层回边前，存在多条 STORE_ATTR 兄弟赋值语句。
反编译器需逐条纳入外层循环体，不可只保留最后一条或全部丢失。

    for stock in stocks:
        while cond:
            ...
        data.index = time_index       # STORE_ATTR #1
        data.value = count            # STORE_ATTR #2
        data.name = stock             # STORE_ATTR #3
"""


class Data:
    def __init__(self):
        self.index = None
        self.value = 0
        self.name = ''


def f(stocks, time_index, count):
    order_data = {}
    for stock in stocks:
        data = Data()
        i = 0
        while i < len(stock):
            i += 1
        data.index = time_index
        data.value = count
        data.name = stock
        order_data[stock] = data
    return order_data
