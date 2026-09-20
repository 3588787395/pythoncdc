# -*- coding: utf-8 -*-
"""R14-J 07 then 体以 try/except/**else** 结束（真实代码的 try 形态）。

真实目标：site-packages/IQCommon/profiler_func.pyc `<module>`。
本类要求区分三种 try 形态：try/except（03）、try/except/else（本文件）、
try/finally（08）。三者**全部 MISMATCH** ⇒ 缺陷与 except/else/finally 臂的
存在性无关，只与「then 区内存在一个 TryExcept 区域」有关。

实测（严格尺子）：<module> **MISMATCH**（seq_len 56→54）：产物 `if PY35: import inspect`
后紧跟顶层 try，且 **else 臂内容被并进 try 体**（`wrap = ...` / `inspect2 = ...`
落在 try 块内）——else 语义整体丢失。
"""
import sys

PY3 = sys.version_info[0] == 3
PY35 = PY3 and sys.version_info[1] >= 5
if PY35:
    import inspect
    try:
        import line_profiler_py35
    except ImportError:
        PY35 = False
    else:
        wrap = line_profiler_py35.wrap
        inspect2 = inspect
