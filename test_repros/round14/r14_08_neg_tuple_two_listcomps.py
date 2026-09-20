# -*- coding: utf-8 -*-
"""R14-08 负对照：**tuple 字面量**里两个同级推导式（对照组，正确）。

形状：`([x for x in t], [y for y in u])`，尾部消费者是 `BUILD_TUPLE 2`。
`_expr_build`（comprehension_generator.py:197）含 'BUILD_TUPLE' → 逃逸判据生效
→ 该形状不被焊接，走通用栈重建路径 → 正确。
与 r14_07（BUILD_LIST）一起构成「消费者白名单不完整」这一根因的对照实验。
（set 字面量 `BUILD_SET` 同族，实测也正确，故不单列复现文件。）
期望：MATCH（负对照，必须保持一致）。
"""


def tuple_two_comps(t, u):
    return ([x for x in t], [y for y in u])
