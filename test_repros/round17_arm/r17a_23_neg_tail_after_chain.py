# -*- coding: utf-8 -*-
"""R17-A 23 负对照：尾随语句挪到 **整条链之外**。

形状：for → 干净 if/elif/else，链后三条赋值。这是锚点 01 的「缺陷输出所声称的源码」。
回收出的 else 臂首块是条件跳转，仍会进 `_build_elif_region`，但
inner_merge == merge_（实测 block=44 first_else=62 inner_merge=170 merge_=170），
判据③不成立 ⇒ 两个世界都建 IF_ELIF_CHAIN（正确），实测均 MATCH。
角色：负对照（证明被展平丢掉的是「尾随相对链的位置」这一语义）。"""


def normalize(rows, strict):
    for key, val in rows.items():
        if val is None:
            text = ''
        elif strict and isinstance(val, str):
            text = repr(val)
        else:
            text = str(val)
        pad = len(text) % 4
        text = text + ' ' * pad
        rows[key] = text
    return rows
