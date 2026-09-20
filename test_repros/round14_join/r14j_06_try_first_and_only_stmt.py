# -*- coding: utf-8 -*-
"""R14-J 06 try 是 then 臂的第一条也是唯一一条语句。

真实目标：site-packages/IQCommon/profiler_func.pyc `<module>`（该处 try 前面还有一条
`import inspect`，本文件把它去掉，验证「零前缀」是否仍截断）。

实测（严格尺子）：<module> **MISMATCH**（seq_len 47→45）：产物 = `if PY35: pass` +
无条件执行的 try ⇒ 前缀语句不是承重件，IfRegion 的缺失与臂体内容无关。
"""
import sys

PY3 = sys.version_info[0] == 3
PY35 = PY3 and sys.version_info[1] >= 5
if PY35:
    try:
        import line_profiler_py35
    except ImportError:
        PY35 = False
