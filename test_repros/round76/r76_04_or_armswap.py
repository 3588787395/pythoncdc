# -*- coding: utf-8 -*-
# R76-B 复现（对照 Quote.change_his_to_backward）：for 内 if/elif/else，
# elif 条件 `A or C:`（A=empty 谓词 TRUE 边指向赋值块；C=相等比较，
# 其 FALSE 边同块），else: break（break=POP_TOP+JUMP）。
# 预期缺陷：产物变 `elif A or C(极性未翻): break else: <赋值>`，两臂交换。
def f(data, series, preindex):
    tmpdata = None
    for n in list(series):
        if preindex is None:
            tmpdata = data[:n][:-1]
        elif data[preindex:n].empty or list(data[preindex:n])[-1] == n:
            data2 = data[preindex:n][:-1]
            tmpdata = tmpdata.append(data2)
        else:
            break
        if preindex != n:
            preindex = n
    if preindex:
        tmpdata = tmpdata.append(data[preindex:])
    return tmpdata
