"""repro_10: 综合——外层 for + dict 构造 + 内层 while + 循环尾部 STORE_ATTR + STORE_SUBSCR。

测试 aspect: get_str_data 完整形态缩影。外层 for 循环体内：
1. dict 字面量构造 (data = {'open': ..., 'close': ...})
2. 内层 while 循环 (含 append + i += 1)
3. 循环尾部兄弟语句：data.index = time_index (STORE_ATTR) + order_data[stock] = data (STORE_SUBSCR)
反编译器需保证 dict 构造、内层循环、循环尾部 STORE_ATTR 与 STORE_SUBSCR 全部按序
纳入外层 for 循环体，STORE_ATTR 不丢失。这正是 get_str_data 残留 -3 的完整复现。

    for stock in stocks:
        data = {'open': a, 'close': b}
        while cond:
            time_index.append(v)
            i += 1
        data.index = time_index        # STORE_ATTR  ← 缺失点
        order_data[stock] = data       # STORE_SUBSCR ← 已生成
"""


def f(stocks, time_index):
    order_data = {}
    for stock in stocks:
        a = stock[0]
        b = stock[-1]
        data = {'open': a, 'close': b}
        i = 0
        while i < len(stock):
            time_index.append(stock[i])
            i += 1
        data['index'] = time_index
        order_data[stock] = data
    return order_data
