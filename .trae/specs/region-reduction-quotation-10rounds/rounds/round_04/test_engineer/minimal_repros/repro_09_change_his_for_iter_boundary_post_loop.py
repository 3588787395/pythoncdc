"""repro_09: FOR_ITER 边界提前收敛 + 循环后 if/None 丢失（change_his_to_backward）。

change_his_to_backward 的 -56 指令差异源于 FOR_ITER 目标提前收敛 + 循环后 if/tmpdata/predataindex 丢失。
镜像实际 CFG：
  - for n in indexlist:（主循环）
    - if int(firsttime) > 0: n = n.replace(...)
    - if ...: ...
  - 循环后：if tmpdata is not None: data = tmpdata; return data
  - 含 series.loc[...] + float(...) + BINARY_OP 等复杂表达式
"""


def change_his_to_backward_repro(indexlist, firsttime, data, fields):
    preindex = None
    tmpdata = None
    predataindex = None
    for n in indexlist:
        if int(firsttime) > 0:
            n = n.replace('-', '')
        if preindex is None:
            preindex = n
        else:
            series = data.loc[preindex]
            value = float(series.loc[(preindex, 'exer_backward_a')]) + float(series.loc[(preindex, 'exer_backward_b')])
            data.loc[(predataindex, fields)] = value / 2
            tmpdata.append(data.loc[predataindex:None])
            if tmpdata is not None:
                data = tmpdata
    return data
