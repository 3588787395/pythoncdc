# -*- coding: utf-8 -*-
"""R15-A 09 anchor try in elif arm
09 子 if 的 try 放进 **elif/else** 一侧（臂位置换）。

真实目标：同上 + r14j_09（try 在 else 臂）。
"""

def check_elif(value):
    flag = isinstance(value, str) and value[-1] == 'q'
    if flag:
        value = value
    elif value:
        try:
            flag = bool(value)
        except ValueError:
            flag = False
    return flag
