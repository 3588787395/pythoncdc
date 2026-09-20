# -*- coding: utf-8 -*-
"""R14-J 08 then 体以 try/**finally** 结束（无 except 的 try 形态）。

真实目标：site-packages/IQCommon/profiler_func.pyc `<module>`（真实代码用
try/except/else，本文件换成 try/finally 做形态对照）。
try/finally 在 3.11 里没有 PUSH_EXC_INFO/CHECK_EXC_MATCH  handler 块，
若仍 MISMATCH，则根因不可能在「except handler 块的归属」上。

实测（严格尺子）：<module> **MISMATCH**（seq_len 46→44）：产物 `if PY35: import inspect`
+ 顶层 try/finally ⇒ finally 形态同样受害。
"""
import sys

PY3 = sys.version_info[0] == 3
PY35 = PY3 and sys.version_info[1] >= 5
if PY35:
    import inspect
    try:
        import line_profiler_py35
    finally:
        PY35 = False
