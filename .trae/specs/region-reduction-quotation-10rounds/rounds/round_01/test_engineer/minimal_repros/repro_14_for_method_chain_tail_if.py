"""repro_14: for 循环 + 方法调用链 + 尾部 if/elif（get_str_data 变体）。

复现原始字节码结构：for 循环内含 stock_df.ix[datas[0]] 切片 +
data.loc[i] = {...} 赋值，循环后有 pandas.Panel 构造 + if 分支。
反编译器丢失循环体后半 + 尾部分支。
对应 _identify_loop_regions / _generate_loop + _generate_block_statements。
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
        data = stock_df.loc[dates]
        time_index = []
        for i in dates:
            value = data.loc[i]
            time_index.append(value)
        data.index = time_index
        order_data[stock] = data
    datas_penal = pandas.Panel(order_data, items=['open', 'close', 'high', 'low', 'volume', 'price', 'money'])
    if typet == 6:
        datas_penal = datas_penal.ix[:, :, 'open']
    return datas_penal
