"""repro_08: for + 嵌套 while + STORE_SUBSCR + 循环后 if/None 边界丢失（change_his / get_date_and_count 变体）。

聚焦 for 循环体内含嵌套 while + data.loc[...]=... STORE_SUBSCR 赋值 + append，
循环后紧跟 `if tmpdata is not None: data = tmpdata`。FOR_ITER 目标提前收敛导致
循环体尾段 + 循环后 if/None 整体丢失。本 repro 聚焦 Loop(嵌套 while) 尾边界。
"""


def process_with_while(data, indexlist, fields):
    tmpdata = None
    predataindex = None
    for n in indexlist:
        j = 0
        while j < len(fields):
            series = data.loc[n]
            factor = float(series.loc[n, 'a']) / float(series.loc[n, 'b'])
            data.loc[predataindex, (fields)] = data.loc[predataindex, data.index[-1:]] * factor
            tmpdata.append(data[predataindex:])
            tmpdata = tmpdata
            j = j + 1
    if tmpdata is not None:
        data = tmpdata
    return data
