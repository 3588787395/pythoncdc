# -*- coding: utf-8 -*-
"""R14-J 09 try 嵌在 **else 臂**（而不是 then 臂）。

真实目标：site-packages/IQCommon/profiler_func.pyc `<module>`（真实代码在 then 臂；
本文件把 try 挪到 else 臂，检验缺陷是否 then-arm 特有）。
条件头块完全一样（BoolOp merge 块 = `STORE b | LOAD b | POP_JUMP_IF_FALSE <else>`），
所以 if 区域同样建不出来；差别只是被截断的是 else 区。

实测（严格尺子）：<module> **MISMATCH**（seq_len 49→47）：产物 `if PY35: flag = 1` +
顶层 try/except，`else` 关键字与 if 的假出口一并消失 ⇒ 与臂极性无关。
"""
import sys

PY3 = sys.version_info[0] == 3
PY35 = PY3 and sys.version_info[1] >= 5
if PY35:
    flag = 1
else:
    try:
        import line_profiler_py35
    except ImportError:
        flag = 2
