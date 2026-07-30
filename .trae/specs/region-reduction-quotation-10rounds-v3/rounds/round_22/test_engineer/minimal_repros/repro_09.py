"""repro_09: 内层 while 含 break + 循环尾部 STORE_ATTR 兄弟语句。

测试 aspect: 内层 while 循环含 break 退出，break 退出后、外层 for 回边前存在
STORE_ATTR 兄弟赋值。反编译器需区分 break 退出路径与正常循环退出，循环尾部块
(STORE_ATTR) 仍应纳入外层 for 循环体，不可因 break 跳转结构丢失。

    for stock in stocks:
        while cond:
            if stop:
                break
            ...
        data.index = time_index   # STORE_ATTR，break 退出后的兄弟语句
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
            if stock[i] < 0:
                break
            i += 1
        data.index = time_index
        order_data[stock] = data
    return order_data
