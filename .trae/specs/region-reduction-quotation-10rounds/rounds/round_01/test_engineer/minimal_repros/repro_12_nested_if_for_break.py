"""repro_12: 嵌套 if 内含 for + break + 尾部 return（change_his_to_backward 变体）。

复现原始字节码结构：if typet == 6: 内嵌 for 循环 + break，
循环后 POP_JUMP_FORWARD_IF_NONE + 尾部赋值 data = tmpdata。
反编译器丢失尾部 if/else 分支。
对应 _identify_conditional_regions 嵌套 + _identify_loop_regions break。
"""


def filter_data(typet, data, indexlist):
    tmpdata = None
    if typet == 6:
        for n in indexlist:
            if int(n) > 0:
                tmpdata = data.loc[n]
                break
    if tmpdata is not None:
        data = tmpdata
    else:
        data = data
    return data
