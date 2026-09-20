# -*- coding: utf-8 -*-
"""R16-S 04 anchor minimal two arm loop
最小可触发形状：外层只有 if/else 两臂，else 臂 = 嵌套 if/else + 尾随语句，全在 for 内。

真实目标：r16s_01 的极简版——只要「elif 链的最后一个 else 臂以嵌套 if 开头、
且该嵌套 if 的归并点 (inner_merge) 早于外层归并点 (merge_)」即触发展平。
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
        items[name] = out
    return items
