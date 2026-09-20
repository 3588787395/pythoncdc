# -*- coding: utf-8 -*-
"""R13-C 负对照 2：臂尾区域的出口**不是落空型**（while True + break：唯一出口是无条件
jump），以及臂尾是「普通语句」。两者必须保持 MATCH —— 它们把触发条件从
「臂里有任何子区域」收窄到「臂尾子区域的出口是**落空型**」。

实测（run_all.py，严格尺子）：三个函数均 MATCH。
"""


def while_true_break_arm(c, r, x):
    if c:
        return 1
    elif r:
        while True:
            x = x + 1
            break
    else:
        return 2
    x = 7


def plain_assign_last_arm(c, r, x):
    if c:
        return 1
    elif r:
        x = 5
    x = 7


def arm_ends_with_full_if_else(c, r, x):
    if c:
        return 1
    elif r:
        if x:
            x = 5
        else:
            x = 6
    else:
        return 2
    x = 7
