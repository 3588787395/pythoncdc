# -*- coding: utf-8 -*-
"""R14-J 12 去掉「标志位复读」（`if not PY35:`）后的模块级最小复现。

真实目标：site-packages/IQCommon/profiler_func.pyc `<module>`。
真实源码在 try/except/else 之后还有一个 `if not PY35:` 重新读同一个标志位，
因此「复读使 merge 计算混乱」是本轮任务书里明确要检验的备选假设。
本文件 = r14j_11 的模块级版本（同一个最小形状，只保留 BoolOp 赋值 + if + try）。

实测（严格尺子）：<module> **MISMATCH**（seq_len 29→27，产物 `if b: pass` +
try 提升到顶层）⇒ **复读假设被否决**：没有 `if not b:` 照样截断。
复读只影响表现形态（有复读时是指令数相等的 target_diff，
无复读时是 seq_len 少两条），不影响根因。
"""
a = 1
b = a and 2
if b:
    try:
        c = 1
    except ValueError:
        pass
