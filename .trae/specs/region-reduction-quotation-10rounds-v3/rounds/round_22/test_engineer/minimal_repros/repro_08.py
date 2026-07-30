"""repro_08: 嵌套 dict 构造 + 内层循环 + 循环尾部 STORE_ATTR (接近 get_str_data)。

测试 aspect: 外层 for 循环体内先构造 dict 字面量 (BUILD_CONST_KEY_MAP)，再进入内层
while 循环，内层循环退出后存在 STORE_ATTR 兄弟语句。这是 get_str_data 的近似形态：
dict 构造作为循环主体归约节点，内层循环退出后的 STORE_ATTR 不应被 dict 消费模式建模
吸收或丢弃。

    for stock in stocks:
        data = {'open': a, 'close': b}
        while cond:
            ...
        data.index = time_index        # STORE_ATTR，dict 构造之后的兄弟语句
"""


def f(stocks, time_index):
    order_data = {}
    for stock in stocks:
        a = stock[0]
        b = stock[1]
        data = {'open': a, 'close': b}
        i = 0
        while i < len(stock):
            i += 1
        data['index'] = time_index
        order_data[stock] = data
    return order_data
