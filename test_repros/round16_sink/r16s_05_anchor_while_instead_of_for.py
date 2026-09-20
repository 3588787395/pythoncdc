# -*- coding: utf-8 -*-
"""R16-S 05 anchor while instead of for
把 r16s_04 的 for 换成 while（换循环种类，不改区域结构）。

真实目标：判据④用的是 `_find_enclosing_loop`，对任何循环都成立；若 05 也 MISMATCH，
说明缺陷与循环类型无关，只与「在某个循环里」有关。
"""


def classify(items, flag_a, flag_c, i):
    while i:
        for name, val in items:
            if flag_a:
                out = 1
            else:
                if flag_c:
                    out = val.x
                else:
                    out = val.z
                side = val.w
                out = out + side
            items[name] = out
            i = 0
    return items
