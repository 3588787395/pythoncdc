"""repro_05: for 循环内方法调用链（replace/float/loc/append）+ 循环后语句（change_his_to_backward）。

原始 change_his_to_backward 循环体含 n.replace('-', '')、float(series.loc[...])、
data.loc[...] = ... * factor、tmpdata.append(data[...]) 等方法调用链。反编译器在
循环体含连续方法调用链 + subscript 赋值时，FOR_ITER 边界提前。本 repro 聚焦
Loop 体内复杂方法链边界缺陷。
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
        factor = float(series.loc[preindex, 'exer_backward_a']) / float(series.loc[preindex, 'exer_backward_b'])
        data.loc[predataindex, 'fields'] = data.loc[predataindex, 'last'] * factor
        tmpdata.append(data[predataindex:])
    if tmpdata is not None:
        data = tmpdata
    return data
