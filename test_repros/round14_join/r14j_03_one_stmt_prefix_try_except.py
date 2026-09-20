# -*- coding: utf-8 -*-
"""R14-J 03 真实形状最小化：then 体 = 一条 import + try/except（无 else 臂、无标志位复读）。

真实目标：site-packages/IQCommon/profiler_func.pyc `<module>`（同 IQData/utils/profiler_func.pyc）。
本文件证明两件事：
  1. try/except 的 **else 臂不是必要条件** —— 只有 except 也照样截断
     （真实代码带 else，是红鲱鱼）；
  2. 后续的 `if not PY35:` 复读**不是必要条件**（见 12 号同结论）。

实测（严格尺子）：<module> **MISMATCH**（seq_len 51→49）：产物 = `if PY35: import inspect`
+ 顶层 try，即真实缺陷产物 profiler_funcOK.py 第 18-28 行的逐字形态。
"""
import sys

PY3 = sys.version_info[0] == 3
PY35 = PY3 and sys.version_info[1] >= 5
if PY35:
    import inspect
    try:
        import line_profiler_py35
    except ImportError:
        line_profiler_py35 = None
