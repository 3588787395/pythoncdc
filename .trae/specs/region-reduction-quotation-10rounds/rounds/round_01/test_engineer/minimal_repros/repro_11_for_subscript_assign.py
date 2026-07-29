"""repro_11: for 循环 + subscript 赋值 + dict 构造（get_str_data 变体）。

复现原始字节码结构：for 循环内含 data.loc[i] = {...} 的 BUILD_CONST_KEY_MAP +
STORE_SUBSCR 模式，循环后有 pandas.Panel 构造。
反编译器丢失循环体内 subscript 赋值（少指令）。
对应 _identify_loop_regions / _generate_loop + _generate_block_statements。
"""
import pandas
import collections


def build_panel(rdata):
    order_data = collections.OrderedDict()
    for stock in rdata:
        data = {}
        for i in range(10):
            data[i] = {'open': 1, 'close': 2, 'high': 3, 'low': 4, 'volume': 5, 'money': 6}
        order_data[stock] = data
    return pandas.Panel(order_data, items=['open', 'close', 'high', 'low', 'volume', 'money'])
