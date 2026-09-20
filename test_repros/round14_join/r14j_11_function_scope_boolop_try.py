# -*- coding: utf-8 -*-
"""R14-J 11 同一形状放进**函数作用域**（对照组：真实案例在模块作用域）。

真实目标：site-packages/IQCommon/profiler_func.pyc `<module>`。
模块级用 LOAD_NAME/STORE_NAME、函数级用 LOAD_FAST/STORE_FAST，
且模块级的异常表与 `if` 的假出口块布局不同。本文件用于确认缺陷
**不是模块作用域特有**：若是，修复合并/归属时就要按 scope 分支。

实测（严格尺子）：`<module>.f` **MISMATCH**（seq_len 29→27）⇒ scope 无关，
禁止用 LOAD_NAME/LOAD_FAST 之类作用域特判去修。
"""


def f():
    a = 1
    b = a and 2
    if b:
        try:
            c = 1
        except ValueError:
            b = 0


CO_GENERATOR = 32
