"""repro_04: dict 构造含三元 + 普通载入（get_str_data 7 键缩影）。

get_str_data 的 dict 有 7 键：4 个普通 LOAD + 2 个三元 + 1 个普通 LOAD。
BUILD_CONST_KEY_MAP 7 消费 7 个栈上值。当前仅识别 2 个 TernaryRegion，
其余 5 个普通 LOAD 未作为 dict value 嵌入。
"""

import numpy


def f(df, i, cond):
    data = {}
    data.loc[i] = {
        'open': df[0],
        'close': df[1],
        'high': df[2].max(),
        'low': df[3].min(),
        'volume': numpy.nan if cond == 1 else df[4].sum(),
        'price': df[5],
        'money': numpy.nan if cond == 1 else df[6].sum(),
    }
    return data
