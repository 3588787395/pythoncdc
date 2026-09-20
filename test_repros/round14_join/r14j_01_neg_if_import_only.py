# -*- coding: utf-8 -*-
"""R14-J 01 负对照：`if c: import x` 单独存在（无嵌套 try）。

真实目标：site-packages/IQCommon/profiler_func.pyc 的 `<module>` 作用域
（同一份源文件的第二份编译产物：site-packages/IQData/utils/profiler_func.pyc）。
被测缺陷类：`if` 臂体含 try/except 时 then 区被截断。

本形状 = 真实代码 `if PY35: import inspect` 的前半（只有 import，没有 try），
用于证明「then 体只有一条 import」本身是无害的，缺陷必须由 try 区域参与才触发。

实测（run_all.py + _r10_strict_check 严格尺子）：<module> **MATCH**（语义指令 20=20，零差异）。
"""
import sys

c = sys.argv
if c:
    import json
