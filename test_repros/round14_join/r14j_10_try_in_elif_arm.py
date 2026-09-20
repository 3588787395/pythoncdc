# -*- coding: utf-8 -*-
"""R14-J 10 try 嵌在 **elif 臂**（BoolOp 仍紧邻 if 头块）。

真实目标：site-packages/IQCommon/profiler_func.pyc `<module>`（真实代码在 then 臂）。
`if PY35:` 的头块仍是 BoolOp merge 块（同一个病根），但这次带 try 的是 **elif 臂**：
IfRegion/IF_ELIF_CHAIN 在候选阶段就被跳过，整条链塌成顺序语句。

实测（严格尺子）：<module> **MISMATCH**（seq_len 54→52，产物没有 elif，
`a = 1` 与 try 都被提到顶层）⇒ elif 臂与 then/else 臂同等受害。
"""
import sys

PY3 = sys.version_info[0] == 3
PY35 = PY3 and sys.version_info[1] >= 5
if PY35:
    a = 1
elif sys.argv:
    try:
        import line_profiler_py35
    except ImportError:
        a = 2
