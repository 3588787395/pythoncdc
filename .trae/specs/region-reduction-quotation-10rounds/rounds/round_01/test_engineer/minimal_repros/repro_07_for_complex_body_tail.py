"""repro_07: for 循环复杂体 + 尾部数据操作丢失（change_his_to_backward 模式）。

复现原始字节码结构：for 循环遍历 indexlist，循环体含 replace / float / loc /
BINARY_SUBSCR / append 调用链，循环后有 POP_JUMP_FORWARD_IF_NONE + 尾部赋值。
反编译器丢失循环体后半 + 尾部 56 条指令。
对应 _identify_loop_regions / _generate_loop 循环体归约边界。
"""


def change_his_to_backward(data, indexlist, fields, exrights):
    preindex = None
    tmpdata = None
    predataindex = None
    for n in indexlist:
        if int(n) > 0:
            n = n.replace('-', '')
        preindex = n
        series = data.loc[n]
        if series is not None:
            value = float(series.loc[preindex, 'exer_backward_a']) - float(series.loc[preindex, 'exer_backward_b'])
            value = value / 2
            data.loc[preindex, fields] = value
            tmpdata.append(data.loc[predataindex:preindex].index[-1:][fields])
    if tmpdata is not None:
        data = tmpdata
    return data
