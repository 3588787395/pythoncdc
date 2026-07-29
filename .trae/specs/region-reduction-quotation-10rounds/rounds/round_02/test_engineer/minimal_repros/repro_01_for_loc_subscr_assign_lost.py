"""repro_01: for 循环内 data.loc[i] = {常量键字典} 赋值丢失（get_str_data 模式）。

原始 get_str_data 中 `data.loc[i] = {'open': ..., 'close': ..., ...}`（BUILD_CONST_KEY_MAP 7 +
STORE_SUBSCR）被反编译器丢弃，循环体后段变为裸表达式。本 repro 聚焦该 Loop 体内
subscript 赋值丢失缺陷。
"""
import pandas


def get_str_data(rdata, count, typet):
    order_data = {}
    for stock, stock_df in rdata.items():
        datetime_index = stock_df.index
        dates = []
        for i in datetime_index:
            dates.append(i)
        data = pandas.DataFrame(columns=['open', 'close', 'high', 'low', 'volume'])
        time_index = []
        for datas in dates[-count:]:
            if not datas:
                continue
            vol = stock_df['volume'].sum()
            money = stock_df['money'].sum()
            data.loc[i] = {'open': vol, 'close': vol, 'high': vol, 'low': vol, 'volume': vol}
            time_index.append(datetime_index[datas])
            i += 1
        order_data[stock] = data
    datas_penal = pandas.Panel(order_data, items=['open', 'close', 'high', 'low', 'volume'])
    return datas_penal
