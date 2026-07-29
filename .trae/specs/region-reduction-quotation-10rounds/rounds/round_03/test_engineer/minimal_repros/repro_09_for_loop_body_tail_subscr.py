"""repro_09: for 循环体尾段 STORE_SUBSCR + append 丢失（change_his_to_backward 变体）。

FOR_ITER 目标被提前收敛，循环体尾段（data.loc[idx] = ... / list.append）丢失。
本 repro 用更精简的形式聚焦 Loop 体尾边界判定：循环体末尾的 STORE_SUBSCR 赋值
与 append 调用被切到循环外或丢弃。
"""


def process_rows(data, indexlist, fields):
    tmpdata = None
    predataindex = None
    for n in indexlist:
        series = data.loc[n]
        factor = float(series.loc[n, 'a']) / float(series.loc[n, 'b'])
        data.loc[predataindex, (fields)] = data.loc[predataindex, data.index[-1:]] * factor
        tmpdata.append(data[predataindex:])
        tmpdata = tmpdata
    if tmpdata is not None:
        data = tmpdata
    return data
