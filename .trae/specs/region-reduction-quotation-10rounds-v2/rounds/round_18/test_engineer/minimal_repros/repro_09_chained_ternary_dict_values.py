"""repro_09: 链式三元 dict 值 + numpy.nan 分支。

演示 get_str_data 中 numpy.nan if data_is_nan == 1 else ... 的模式。
每个键值的三元都有 numpy.nan 作为 if 分支。
"""
import numpy


def f(data, i, data_is_nan, stock_df, datas):
    data.loc[i] = {
        'open': numpy.nan if data_is_nan == 1 else stock_df[datas].max(),
        'close': numpy.nan if data_is_nan == 1 else stock_df[datas][-1],
        'volume': numpy.nan if data_is_nan == 1 else stock_df[datas].sum(),
    }
