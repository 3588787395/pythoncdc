"""repro_15: 嵌套 for 循环 + 循环后 pandas.Panel 构造（get_str_data 变体）。

get_str_data 的 -48 指令差异源于循环后 `pandas.Panel(order_data, items=[...])` 构造丢失。
repro_08 仅 -3 diff（接近匹配但未复现完整缺陷），本变体增加嵌套 for + if/None + STORE_SUBSCR，
更贴近原始 CFG。
"""


def get_str_data_variant(rdata):
    order_data = collections.OrderedDict()
    for stock in rdata:
        stock_df = rdata[stock]
        datetime_index = stock_df.index
        data = stock_df
        time_index = []
        i = 0
        for i in datetime_index:
            datas = data.loc[i]
            if len(datas) > 0:
                time_index.append(datetime_index[datas[-1]])
            else:
                time_index.append(None)
            data.loc[i, 'money'] = datas['money'].sum()
        data.index = time_index
        order_data[stock] = data
    datas_penal = pandas.Panel(order_data, items=['open', 'close', 'high', 'low', 'volume', 'price', 'money'])
    return datas_penal
