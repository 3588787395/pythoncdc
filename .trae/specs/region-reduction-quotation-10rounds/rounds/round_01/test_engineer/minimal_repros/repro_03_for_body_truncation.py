"""repro_03: for 循环遍历 dict.items() + 嵌套 for + 循环后构造（get_str_data 模式）。

复现原始字节码结构：for stock, stock_df in rdata.items() 内嵌 for 循环
+ subscript 赋值 order_data[stock] = data，循环后有 pandas.Panel 构造。
反编译器丢失循环体 + 循环后语句（少 53 条）。
对应 _identify_loop_regions 嵌套 for + _generate_loop + _generate_basic_region。
"""
import pandas
import collections


def get_str_data(rdata):
    order_data = collections.OrderedDict()
    for stock, stock_df in rdata.items():
        datetime_index = stock_df.index
        dates = []
        for i in datetime_index:
            dates.append(i)
        data = stock_df.loc[dates]
        time_index = []
        i = 0
        for d in dates:
            time_index.append(datetime_index[d])
            i = i + 1
        data.index = time_index
        order_data[stock] = data
    datas_penal = pandas.Panel(order_data, items=['open', 'close', 'high', 'low', 'volume', 'price', 'money'])
    return datas_penal
