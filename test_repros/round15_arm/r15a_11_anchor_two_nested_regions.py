# -*- coding: utf-8 -*-
"""R15-A 11 anchor two nested regions
11 子 if 的 then 臂含**两个**结构区域（try 之后还有 for）。

真实目标：同上。检验「臂止步」后剩余语句是否被正确顺序挂回。
"""

def check_two(value):
    if value is None:
        flag = True
    else:
        flag = isinstance(value, str) and value[-1] == 'q'
        if flag:
            try:
                flag = bool(value)
            except ValueError:
                flag = False
            for i in value:
                flag = bool(i)
    return flag
