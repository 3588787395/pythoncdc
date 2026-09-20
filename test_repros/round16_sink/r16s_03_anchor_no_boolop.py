# -*- coding: utf-8 -*-
"""R16-S 03 anchor no boolop
去掉 all BoolOp 条件（`A and B`）与 hasattr/CALL，条件全为**简单名称测试**，
保留「else 臂 = 嵌套 if/elif/else + 尾随语句」这一结构。

真实目标：证明触发成分只有区域结构，不需要 BoolOp 短路链参与。
"""


def pick(items, flag_a, flag_b, flag_c, flag_d):
    for name, val in items:
        if flag_a:
            out = 1
        elif flag_b:
            out = 2
        else:
            if flag_c:
                out = val.x
            elif flag_d:
                out = val.y
            else:
                out = val.z
            side = val.w
            out = out + side
        items[name] = out
    return items
