"""repro_07: 循环尾部 STORE_ATTR 后跟方法调用表达式语句。

测试 aspect: 内层循环退出后的兄弟语句中，STORE_ATTR 之后紧跟方法调用表达式语句
(POP_TOP 消费)。反编译器需保证 STORE_ATTR 与后续 expr 语句均纳入外层循环体，
不因 POP_TOP 语句边界识别吞并前导 STORE_ATTR。

    for stock in stocks:
        while cond:
            ...
        data.index = time_index          # STORE_ATTR
        time_index.append(value)         # expr stmt (POP_TOP)
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
            i += 1
        data.index = time_index
        time_index.append(stock)
        order_data[stock] = data
    return order_data
