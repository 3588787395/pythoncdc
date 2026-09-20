# -*- coding: utf-8 -*-
"""R13-C 负对照 1：**两个**臂都能落空到链尾（其中至少一个以普通语句落空）。
此时 merge 块有链内多前驱，现有实现能正确算出 merge —— 必须保持 MATCH，
否则说明修复把判据放宽成「见链就改」。

实测（run_all.py，严格尺子）：两个函数均 MATCH。
"""


def two_fallthrough_arms(c, r, x):
    if c:
        for d in r:
            x = x + d
    elif r:
        x = 1
    else:
        return 2
    x = 7


def two_loop_arms(c, r, x):
    if c:
        for d in r:
            x = x + d
    elif r:
        for d in r:
            x = x - d
    else:
        return 2
    x = 7
