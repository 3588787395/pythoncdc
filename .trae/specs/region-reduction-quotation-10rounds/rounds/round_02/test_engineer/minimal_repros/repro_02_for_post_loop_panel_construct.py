"""repro_02: for 循环体 + 循环后构造语句丢失（get_str_data 尾部 Panel 构造）。

原始 get_str_data 的 FOR_ITER 目标 1546 被反编译器收敛为 1214，导致循环后半段
（time_index.append / order_data[stock] = data）+ 循环后 pandas.Panel(order_data, items=[...])
构造整体丢失。本 repro 聚焦 Loop 循环后语句边界判定缺陷。
"""
import pandas
import collections


def get_str_data(rdata, count, typet):
    order_data = collections.OrderedDict()
    for stock, stock_df in rdata.items():
        datetime_index = stock_df.index
        dates = []
        for i in datetime_index:
            dates.append(i)
        data = pandas.DataFrame(columns=['open', 'close', 'high', 'low', 'volume', 'money'])
        time_index = []
        n = stock_df.iloc[:, 0].size
        for datas in dates[-count:]:
            if not datas:
                continue
            value = stock_df['volume'].sum()
            money = stock_df['money'].sum()
            time_index.append(datetime_index[datas])
        data.index = time_index
        order_data[stock] = data
    datas_penal = pandas.Panel(order_data, minor_axis=['open', 'close', 'high', 'low', 'volume', 'money'])
    return datas_penal
