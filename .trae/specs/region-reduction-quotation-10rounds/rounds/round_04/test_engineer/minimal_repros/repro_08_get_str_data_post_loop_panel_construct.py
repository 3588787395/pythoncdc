"""repro_08: 循环后 `pandas.Panel(...)` 构造边界丢失（get_str_data）。

get_str_data 的 -48 指令差异源于循环后 `pandas.Panel(order_data, items=[...])` 构造丢失。
镜像实际 CFG：
  - for stock, stock_df in rdata.items():（主循环）
    - for i in datetime_index:（内层循环）
      - if ...: datas.loc[i] = ...
      - i += 1
    - time_index.append(...)
    - data.index = time_index
    - order_data[stock] = data
  - 循环后：datas_penal = pandas.Panel(order_data, items=['open', 'close', ...])
  - return datas_penal
"""


def get_str_data_repro(rdata):
    order_data = collections.OrderedDict()
    for stock in rdata:
        stock_df = rdata[stock]
        datetime_index = stock_df.index
        dates = []
        data = stock_df
        time_index = []
        for i in datetime_index:
            datas = data.loc[i]
            if len(datas) > 0:
                time_index.append(datetime_index[datas])
            i = i + 1
        data.index = time_index
        order_data[stock] = data
    datas_penal = pandas.Panel(order_data, items=['open', 'close', 'high', 'low', 'volume', 'price', 'money'])
    return datas_penal
