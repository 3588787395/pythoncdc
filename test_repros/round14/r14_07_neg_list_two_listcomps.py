# -*- coding: utf-8 -*-
"""R14-07 负对照：**list 字面量**里两个同级推导式（对照组，正确）。

形状 A：`[[x for x in t], [y for y in u]]`（两个 list 推导式）
形状 B：`[{x: x for x in t}, {y: y for y in u}]`（两个 dict 推导式）
两者的尾部消费者都是 `BUILD_LIST 2`。与 dict 版（r14_01/r14_12）唯一的差别
就是这一个消费者 opcode：`comprehension_generator.py:197` 的逃逸判据
`_expr_build` 含 'BUILD_LIST'，于是焊接前 return None，走通用栈重建路径 → 正确。
这条对照是根因的直接证据：**同一个成对探测器，只是消费者 opcode 不同**。
期望：MATCH（负对照，必须保持一致）。
"""


def list_two_comps(t, u):
    return [[x for x in t], [y for y in u]]


def list_two_dictcomps(t, u):
    return [{x: x for x in t}, {y: y for y in u}]
