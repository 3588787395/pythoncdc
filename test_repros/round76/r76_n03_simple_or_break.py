# -*- coding: utf-8 -*-
# 负对照：for 内 `if A or B: break else: 赋值`（两操作数的 TRUE 边
# 同收敛到 break 路径 —— 同构链，非 R76-B 异构形态）。
def f(data, series):
    out = []
    for n in series:
        if data[n] is None or data[n] < 0:
            break
        else:
            out.append(data[n])
    return out
