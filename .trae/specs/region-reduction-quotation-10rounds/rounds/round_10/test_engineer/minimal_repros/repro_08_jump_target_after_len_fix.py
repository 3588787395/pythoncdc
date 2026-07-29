"""R10 repro_08: change_his_to_backward 跳转目标归一化差异（instr_diff@296，R9 已修复 len）。
缺陷: for 循环内嵌套 if 的 else 体已恢复(R9)，残留跳转目标偏移(语义等价)。
区域类型: Loop + Conditional  违反原则: 4(入口引用语义)
"""
def f(indexlist, data):
    predataindex = None
    tmpdata = None
    for n in indexlist:
        if predataindex is None:
            tmpdata = data[:n].copy()
            predataindex = n
        elif n in data.index:
            y = n + 'end'
            if len(data[predataindex:y]) == 0:
                pass
            else:
                tmpdata = tmpdata.append(data[predataindex:y])
        else:
            tmpdata = tmpdata.append(data[predataindex:n])
    return tmpdata
