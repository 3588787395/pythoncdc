# -*- coding: utf-8 -*-
"""R16-S 07 neg tail after chain
把尾随语句挪到 **整条 if/elif/else 链之外**（即 r16s_04 缺陷输出所「声称」的源码）。
此时所有臂的归并点就是尾随语句入口，inner_merge == merge_，是真 elif 链。

真实目标：证明缺陷输出不是等价改写而是语义改写——同一份 CFG 只能由
「else 臂内嵌套 + 尾随」产生；把它当源码编译回去，then/elif 臂的 JUMP_FORWARD
终点会落到尾随语句（= 正确），而原 pyc 里该跳转越过尾随语句。本文件必须 MATCH，
说明「尾随语句相对链的位置」才是被丢掉的语义。
"""


def classify(items, flag_a, flag_c, flag_d):
    for name, val in items:
        if flag_a:
            out = 1
        elif flag_c:
            out = val.x
        else:
            out = val.z
        side = val.w
        out = out + side
        items[name] = out
    return items
