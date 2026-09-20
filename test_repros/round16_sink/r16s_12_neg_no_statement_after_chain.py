# -*- coding: utf-8 -*-
"""R16-S 12 neg no statement after chain
r16s_04 删掉链尾的 `items[name] = out`，使**外层归并点就是循环回边**（merge_ 为 None
或循环尾），嵌套 if 的 inner_merge 也就是链尾。

真实目标：证明 D2 判据②（`merge_ is not None`）也是必要成分——外层没有独立归并点时
「尾随语句」根本不存在，展平不会产生终点漂移。
"""


def classify(items, flag_a, flag_c, flag_d):
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
    return items
