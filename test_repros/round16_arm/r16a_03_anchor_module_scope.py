# -*- coding: utf-8 -*-
"""R16-A 03 锚点：同一 entry-steal 形状搬到 **模块作用域**（顶层 if）。

真实目标里 `_is_valid_quarter` 的缺陷块 94 同时是 BoolOp@94 与 Try@94 的入口；
本复现检验同样的机制在 `<module>` 代码对象里是否成立（顶层 no 闭包/无 LOAD_DEREF，
块划分更干净）。若也 MISMATCH ⇒ 与函数作用域无关，是生成层的公共路径。

同时对照：round15 的 r15a_02 用**另一种**（更复杂的）形状在模块作用域复现，
本文件是它在「try 外壳丢失」这一症状下的最小版本。
"""

value = '2018q3'

if value is None:
    valid = True
else:
    valid = isinstance(value, str) and len(value) == 5
    if valid:
        try:
            valid = 1990 <= int(value) <= 9999 and 1 <= int(value) <= 4
        except (ValueError, TypeError):
            valid = False

print(valid)
