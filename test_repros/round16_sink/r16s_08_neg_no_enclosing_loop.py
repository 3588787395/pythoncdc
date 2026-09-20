# -*- coding: utf-8 -*-
"""R16-S 08 neg no enclosing loop
r16s_01/04 的形状**移出任何循环**（函数体内顺序语句）。

真实目标：直接隔离 region_analyzer.py:18748 的判据④
（`and self._find_enclosing_loop(first_else) is None`）。
04 MISMATCH 而 08 MATCH ⇒ 唯一的差别就是「在循环里」，即判据④屏蔽了 D2 否决。
"""


def classify(flag_a, flag_c, flag_d, val, bag):
    if flag_a:
        out = 1
    else:
        if flag_c:
            out = val.x
        elif flag_d:
            out = val.y
        else:
            out = val.z
        side = val.w
        out = out + side
    bag.append(out)
    return bag
