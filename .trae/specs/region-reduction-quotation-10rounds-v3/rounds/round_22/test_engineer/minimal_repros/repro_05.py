"""repro_05: 循环尾部 STORE_ATTR 目标为循环内构造对象 (data.index = time_index)。

测试 aspect: STORE_ATTR 的目标对象 data 在外层 for 循环内构造，属性 index 赋值为
循环外变量 time_index。这是 get_str_data 的实际形态：data 在循环内通过 dict/对象
构造，data.index = time_index 在内层 while 退出后赋值。反编译器需正确重建
STORE_ATTR 目标表达式 (data) 与值表达式 (time_index)。

    for stock in stocks:
        data = build_data()
        while cond:
            ...
        data.index = time_index   # STORE_ATTR，目标为循环内构造的 data
"""


class Data:
    def __init__(self):
        self.index = None
        self.open = 0


def build_data():
    return Data()


def f(stocks, time_index):
    order_data = {}
    for stock in stocks:
        data = build_data()
        i = 0
        while i < 10:
            data.open = i
            i += 1
        data.index = time_index
        order_data[stock] = data
    return order_data
