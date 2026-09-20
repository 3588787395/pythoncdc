# -*- coding: utf-8 -*-
"""R15-A 07 neg no boolop prefix
07 负对照：去掉值上下文 BoolOp（前缀改成普通赋值），臂体仍是 try。

真实目标：同上。若 MATCH，则触发者确为「子 if 的入口块被父 BoolOp 区域当成 merge 块」，
而不是「臂体里有 try」。
"""

def check_no_boolop(value):
    if value is None:
        flag = True
    else:
        flag = isinstance(value, str)
        if flag:
            try:
                flag = 1990 <= int(value) <= 9999
            except (ValueError, TypeError):
                flag = False
    return flag
