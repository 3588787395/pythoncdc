# -*- coding: utf-8 -*-
"""R14-J 04 then 体 = 普通赋值 + try/except（臂体首条语句不是 import）。

真实目标：site-packages/IQCommon/profiler_func.pyc `<module>`。
用于排除「import/IMPORT_NAME 特殊性」这一备选解释：把臂体首条语句换成
普通赋值，缺陷照样发生 ⇒ 触发者与语句类型无关，只与
「then 区里出现了第二个区域（TryExceptRegion）」有关。

实测（严格尺子）：<module> **MISMATCH**（seq_len 49→47）：产物 then 体只剩 `flag = 1`，
try 区成为 `if` 的兄弟区域。
"""
import sys

PY3 = sys.version_info[0] == 3
PY35 = PY3 and sys.version_info[1] >= 5
if PY35:
    flag = 1
    try:
        import line_profiler_py35
    except ImportError:
        line_profiler_py35 = None
