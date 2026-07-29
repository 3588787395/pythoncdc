"""repro_16: 嵌套 for + 字典常量键赋值 + 循环后构造（get_str_data 变体）。

原始 get_str_data 中嵌套 for 内 `data.loc[i] = {'open':..., 'close':..., ...}`
（BUILD_CONST_KEY_MAP 7 + STORE_SUBSCR）+ 循环后 `order_data[stock] = data` +
`pandas.Panel(order_data, minor_axis=[...])` 构造。反编译器丢失 loc subscript 赋值。
本 repro 聚焦 Loop 嵌套 for + subscript 字典赋值 + 循环后构造边界缺陷。
"""
import pandas
import collections


def get_str_data(rdata, count, typet):
    order_data = collections.OrderedDict()
    for stock, stock_df in rdata.items():
        datetime_index = stock_df.index
        dates = [i for i in datetime_index]
        data = pandas.DataFrame(columns=['open', 'close', 'high', 'low', 'volume', 'money'])
        time_index = []
        for datas in dates[-count:]:
            if not datas:
                continue
            vol = stock_df['volume'].sum()
            money = stock_df['money'].sum()
            data.loc[i] = {'open': vol, 'close': vol, 'high': vol, 'low': vol, 'volume': vol, 'money': money}
            time_index.append(datetime_index[datas])
            i += 1
        order_data[stock] = data
    datas_penal = pandas.Panel(order_data, minor_axis=['open', 'close', 'high', 'low', 'volume', 'money'])
    return datas_penal
