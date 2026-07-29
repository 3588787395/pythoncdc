"""repro_19: for + 嵌套 while + .loc subscript 赋值 + append（change_his_to_backward 变体）。

原始 change_his_to_backward 循环体含 `series = data.loc[preindex]`、
`float(series.loc[preindex, 'exer_backward_a'])` 等连续 .loc subscript + 方法链。
反编译器 FOR_ITER 边界提前。本 repro 聚焦 Loop 体内连续 .loc subscript + while 边界缺陷。
"""


def change_his_to_backward(security, data, exrights_data, start, end, typet):
    indexlist = exrights_data.index
    preindex = None
    tmpdata = []
    predataindex = None
    for n in indexlist:
        if int(start) > 0:
            n = n.replace('-', '')
        series = data.loc[preindex]
        j = 0
        while j < len(series):
            factor = float(series.loc[preindex, 'exer_backward_a']) / float(series.loc[preindex, 'exer_backward_b'])
            data.loc[predataindex, 'fields'] = data.loc[predataindex, 'last'] * factor
            j += 1
        tmpdata.append(data[predataindex:])
    if tmpdata is not None:
        data = tmpdata
    return data
