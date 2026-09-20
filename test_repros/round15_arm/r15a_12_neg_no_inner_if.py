# -*- coding: utf-8 -*-
"""R15-A 12 neg no inner if
12 负对照：只保留外层 if + BoolOp 前缀 + try（**没有**中间那条 if）。

真实目标：同上。作为 01 的直接对照：01 MISMATCH 而本文件 MATCH 才能把缺陷归给
中间那条 if 的归属，而不是 try 或 BoolOp 本身。
"""

def check_no_inner(value):
    if value is None:
        flag = True
    else:
        flag = isinstance(value, str) and value[-1] == 'q'
        try:
            flag = 1990 <= int(value) <= 9999
        except (ValueError, TypeError):
            flag = False
    if not flag:
        raise ValueError(value)
    return flag
