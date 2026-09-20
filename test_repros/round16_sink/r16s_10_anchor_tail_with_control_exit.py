# -*- coding: utf-8 -*-
"""R16-S 10 anchor tail with control exit
r16s_04 的尾随语句里加一条 **循环控制出口**（`if flag_d: break`），
使 inner_merge 之后存在额外的循环退出路径。

真实目标：判据④的原始理由是「循环内 break/continue 使 inner_merge 合法地不等于
merge_」（R24-A）。本文件是那条理由的直接检验：若它也 MISMATCH，说明豁免④
连自己想保护的场景都没保住；若 MATCH，则 04 与 10 的差集给出精确的豁免边界。
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
            if flag_d:
                break
        items[name] = out
    return items
