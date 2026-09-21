# -*- coding: utf-8 -*-
"""R17-A 22 negative nested if + trailing in the THEN arm.

把 01 的「嵌套 if/else + 尾随赋值」整体搬进 **then 臂**（else 臂只剩一条赋值）。
elif 归并只作用于回收出来的 else 臂（`first_else`），then 臂不进入
`_build_elif_region`，因此删④与本形状无关。

角色：负对照（限定触发面 = else 臂）。
"""


def normalize(rows, strict):
    for key, val in rows.items():
        if val is None:
            if strict and isinstance(key, str):
                text = ''
            else:
                text = 'x'
            pad = len(text) % 4
            text = text + ' ' * pad
        else:
            text = str(val)
        rows[key] = text
    return rows
