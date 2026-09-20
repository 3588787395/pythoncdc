# -*- coding: utf-8 -*-
"""R14-J 05 then 体 = 两条赋值 + try/except（前缀长度 2 是否仍截断）。

真实目标：site-packages/IQCommon/profiler_func.pyc `<module>`。
问题：截断点固定在「臂体第一条语句」还是「臂体最后一个非 try 语句之前」？
实测（严格尺子）：<module> **MISMATCH**（seq_len 51→49），且产物**保留全部两条**前缀
语句（`flag = 1; other = 2`）、只把 try 区甩到 `if` 外 ⇒ 截断点 = 「then 区里第一个
不属于本区域的块」，与臂体前缀长度无关（r14j_03/04/05 三点同构）。
"""
import sys

PY3 = sys.version_info[0] == 3
PY35 = PY3 and sys.version_info[1] >= 5
if PY35:
    flag = 1
    other = 2
    try:
        import line_profiler_py35
    except ImportError:
        line_profiler_py35 = None
