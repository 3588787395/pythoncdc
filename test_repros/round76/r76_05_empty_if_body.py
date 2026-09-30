# -*- coding: utf-8 -*-
# R76-C 复现（对照 Quote.change_his_to_forward）：for 内 if/elif 链，
# `if <end-match>: pass`（空真体编译为 vacuous POP_JUMP+NOP），其后是
# 同层 `if preindex is None:` 块。预期缺陷：空体 if 吸收后继兄弟块为体，
# elif false 边被改道。
def f(data, preindex, series, start, end):
    for n in list(series):
        if data[preindex:n].empty:
            continue
        elif len(data[preindex:n].index) == 1:
            if list(data[preindex:n].index)[0] == start:
                continue
            if list(data[preindex:n].index)[0] == end:
                pass
        if preindex is None:
            tmpdata = data[preindex:n]
            if tmpdata[n:].empty:
                tmpdata = tmpdata
            else:
                tmpdata = tmpdata[:-1]
        else:
            tmp2 = data[preindex:n]
            tmpdata = tmpdata.append(tmp2)
        if preindex != n:
            preindex = n
    return data
