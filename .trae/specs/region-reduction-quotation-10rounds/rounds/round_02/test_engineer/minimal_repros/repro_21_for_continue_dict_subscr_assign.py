"""repro_21: for + continue + BUILD_CONST_KEY_MAP subscript 赋值（get_str_data 变体）。

原始 get_str_data 循环体含 `if not datas: continue` + `data.loc[i] = {'open':..., ...}`
（BUILD_CONST_KEY_MAP + STORE_SUBSCR）。反编译器在 continue + 字典 subscript 赋值
组合下丢失 STORE_SUBSCR。本 repro 聚焦 Loop 体内 continue + 字典 subscript 赋值缺陷。
"""
import pandas


def get_str_data(rdata, count, typet):
    order_data = {}
    for stock, stock_df in rdata.items():
        datetime_index = stock_df.index
        dates = [i for i in datetime_index]
        data = pandas.DataFrame(columns=['open', 'close', 'high', 'low', 'volume', 'money'])
        for datas in dates[-count:]:
            if not datas:
                continue
            vol = stock_df['volume'].sum()
            money = stock_df['money'].sum()
            data.loc[i] = {'open': vol, 'close': vol, 'high': vol, 'low': vol, 'volume': vol, 'money': money}
            i += 1
        order_data[stock] = data
    return order_data
