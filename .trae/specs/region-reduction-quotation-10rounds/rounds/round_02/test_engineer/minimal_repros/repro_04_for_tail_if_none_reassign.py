"""repro_04: for 循环 + 尾部 POP_JUMP_FORWARD_IF_NONE 重赋值丢失（change_his_to_backward 尾部）。

原始 change_his_to_backward 循环后段：
    tmpdata.append(data[predataindex:])
    if tmpdata is not None:      # POP_JUMP_FORWARD_IF_NONE
        data = tmpdata
    return data
反编译器把循环后 if/None 重赋值 + return 丢失，提前 return data。本 repro 聚焦
Loop 循环后 None 判定重赋值边界缺陷。
"""


def filter_data(security, data, exrights_data):
    indexlist = exrights_data.index
    preindex = None
    tmpdata = None
    for n in indexlist:
        n = n.replace('-', '')
        series = data.loc[preindex]
        factor = float(series.loc[preindex, 'a']) / float(series.loc[preindex, 'b'])
        tmpdata.append(data[n:])
    if tmpdata is not None:
        data = tmpdata
    return data
