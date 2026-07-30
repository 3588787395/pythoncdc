"""repro_06: 内层循环与外层回边间多条异构兄弟语句。

测试 aspect: 内层 while 退出后、外层 for 回边前，存在 3+ 条异构兄弟语句：
- STORE_ATTR 赋值
- STORE_FAST 赋值
- 表达式语句 (POP_TOP)
- STORE_SUBSCR 赋值
反编译器需按原始顺序逐条纳入外层循环体，不可遗漏中间语句。

    for stock in stocks:
        while cond:
            ...
        data.index = time_index       # STORE_ATTR
        flag = check(data)            # STORE_FAST
        log.append(stock)             # expr stmt (POP_TOP)
        order_data[stock] = data      # STORE_SUBSCR
"""


class Data:
    def __init__(self):
        self.index = None


def check(d):
    return d.index is not None


def f(stocks, time_index, log):
    order_data = {}
    for stock in stocks:
        data = Data()
        i = 0
        while i < len(stock):
            i += 1
        data.index = time_index
        flag = check(data)
        log.append(stock)
        order_data[stock] = data
    return order_data
