# -*- coding: utf-8 -*-
"""R15-A 05 anchor nested for
05 嵌套 if 的臂体换成 **for 循环**（结构区域类型再推广）。

真实目标：同上。若 for 也触发，则缺陷与 Try 无关，是臂边界通病。
"""

def check_for(value):
    if value is None:
        flag = True
    else:
        flag = isinstance(value, str) and value[-1] == 'q'
        if flag:
            for i in value:
                flag = bool(i)
    return flag
