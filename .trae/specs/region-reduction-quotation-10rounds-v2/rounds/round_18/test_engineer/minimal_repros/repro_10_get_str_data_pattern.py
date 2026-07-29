"""repro_10: get_str_data 完整模式缩影。

模拟 get_str_data 的核心循环结构：循环中 data.loc[i] = {7 键三元}，
i 递增，包含 BUILD_CONST_KEY_MAP + STORE_SUBSCR 完整模式。
"""
import numpy


def f(rdata, count, typet):
    order_data = {}
    for stock in rdata:
        stock_df = rdata[stock]
        n = len(stock_df)
        data = {}
        i = 0
        for j in range(n):
            data_is_nan = j % 2
            data.loc[i] = {
                'open': numpy.nan if data_is_nan == 1 else stock_df[j],
                'close': numpy.nan if data_is_nan == 1 else stock_df[j],
                'high': numpy.nan if data_is_nan == 1 else stock_df[j],
                'low': numpy.nan if data_is_nan == 1 else stock_df[j],
                'volume': numpy.nan if data_is_nan == 1 else stock_df[j],
                'price': numpy.nan if data_is_nan == 1 else stock_df[j],
                'money': numpy.nan if data_is_nan == 1 else stock_df[j],
            }
            i += 1
        order_data[stock] = data
    return order_data
