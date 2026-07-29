"""R9 repro_01: change_his_to_backward for 循环内嵌套 if 的 else 分支体丢失。
缺陷: for 循环体内 `if len(...)==0:` 的 else 分支体整段丢失(变 pass)，
根因 _if_generate_then_branch 用 _if_generate_else_branch 作探针有副作用(预标记 generated_blocks)，
正规调用时 else 块已标记为已生成而返回空。
区域类型: Loop + Conditional  违反原则: 2(每块唯一归属) + 4(入口引用语义)
"""
def f(indexlist, data, series, fields):
    preindex = None
    tmpdata = None
    predataindex = None
    for n in indexlist:
        if preindex is None:
            tmpdata = data[:n].copy()
            preindex = n
            predataindex = n
        elif data[predataindex:n].empty:
            break
        elif n in data.index:
            y = n + 'end'
            if len(data[predataindex:y]) == 0:
                pass
            else:
                data.loc[predataindex:y, fields] = round(data[predataindex:y][fields] * 1.0 + 2.0, 2)
                tmpdata = tmpdata.append(data[predataindex:y])
        else:
            data.loc[predataindex:n, fields] = round(data[predataindex:n][fields] * 1.0 + 2.0, 2)
            tmpdata = tmpdata.append(data[predataindex:n])
    if predataindex and len(data[predataindex:]) > 0:
        tmpdata = tmpdata.append(data[predataindex:])
    return tmpdata
