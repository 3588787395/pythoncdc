"""repro_12: 单层 for 循环体尾段 + 循环后构造语句边界丢失（get_str_data / change_his 变体）。

聚焦单层 for 循环，循环体末尾含 STORE_SUBSCR 赋值 + append，循环后紧跟一个
构造器调用（pandas.DataFrame/Panel）。FOR_ITER 目标提前收敛导致循环体尾段 +
循环后构造整体丢失。本 repro 用单层循环精简定位 Loop 尾边界 + 循环后构造边界。
"""
import pandas


def build_frame(rows, fields):
    result = {}
    tmpdata = None
    preindex = None
    for n in rows:
        series = result.loc[n]
        factor = float(series.loc[n, 'a']) / float(series.loc[n, 'b'])
        result.loc[preindex, (fields)] = result.loc[preindex, result.index[-1:]] * factor
        tmpdata.append(result[preindex:])
        tmpdata = tmpdata
    frame = pandas.DataFrame(result, columns=['open', 'close', 'high', 'low', 'volume', 'money'])
    return frame
