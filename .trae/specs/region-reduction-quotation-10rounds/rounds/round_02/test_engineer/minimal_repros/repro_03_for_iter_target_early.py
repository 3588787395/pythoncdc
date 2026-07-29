"""repro_03: for 循环 FOR_ITER 目标提前收敛 + 循环后语句丢失（change_his_to_backward 模式）。

原始 change_his_to_backward 中 `for n in indexlist:` 的 FOR_ITER 目标 2594 被收敛为 2294，
循环体尾段（series.loc 替换 / data.loc[predataindex] = ... / tmpdata.append）丢失，
循环后 `POP_JUMP_FORWARD_IF_NONE tmpdata` + tmpdata 重赋值 + return 也丢失。
本 repro 聚焦 Loop 边界 + 循环后 if/None 重赋值缺陷。
"""
import pandas


def change_his_to_backward(security, data, exrights_data, start, end, typet):
    indexlist = exrights_data.index
    preindex = None
    tmpdata = None
    predataindex = None
    for n in indexlist:
        if int(firsttime) > 0:
            n = n.replace('-', '')
        series = data.loc[preindex]
        fields = data.loc[predataindex, 'fields']
        factor = float(series.loc[preindex, 'exer_backward_a']) / float(series.loc[preindex, 'exer_backward_b'])
        data.loc[predataindex, (fields)] = data.loc[predataindex, data.index[-1:]] * factor
        tmpdata.append(data[predataindex:])
        tmpdata = tmpdata
    if tmpdata is not None:
        data = tmpdata
    return data
