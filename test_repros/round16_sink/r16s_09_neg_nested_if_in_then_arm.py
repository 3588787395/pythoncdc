# -*- coding: utf-8 -*-
"""R16-S 09 neg nested if plus tail in THEN arm
把 r16s_04 的「嵌套 if + 尾随语句」放进 **then 臂**（而不是 else 臂）。

真实目标：展平机制（_check_elif_chain 的递归 `conditions.extend(deeper_elif)`）
只作用于 else 臂；then 臂不参与 elif 归并。本文件 MATCH 则说明触发面严格限于
「elif 链最后一个 else 臂」。
"""


def classify(items, flag_a, flag_c, flag_d):
    for name, val in items:
        if flag_a:
            if flag_c:
                out = val.x
            else:
                out = val.z
            side = val.w
            out = out + side
        else:
            out = 2
        items[name] = out
    return items
