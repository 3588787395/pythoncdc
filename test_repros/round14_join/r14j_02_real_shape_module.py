# -*- coding: utf-8 -*-
"""R14-J 02 真实形状（还原源码）：`if flag:` 的 then 体 = import + try/except/else。

真实目标：site-packages/IQCommon/profiler_func.pyc `<module>`（15/16 函数干净，
唯一缺陷就是本形状）；同一份源码的另一编译产物 site-packages/IQData/utils/
profiler_func.pyc 形状完全相同（其 BoolOp merge 块 = B166，同样没建 IfRegion）。
产物 site-packages/IQCommon/profiler_funcOK.py 第 18-28 行把 try/except/else
整块甩到了 `if PY35:` 外面（真源码里它在 if 体内）。

实测（严格尺子）：<module> **target_diff** —
`#24 POP_JUMP_IF_FALSE 终点 orig=("'PY35'", 'LOAD_NAME') decomp=('0', 'LOAD_CONST')`，
语义指令数 67=67（一条不丢，只是落点从 `if not PY35:` 挪到了 try 体的 IMPORT_NAME）。
与真实 pyc 的 #82 判据 **逐字同构**（orig=("'PY35'", LOAD_NAME) decomp=('0', LOAD_CONST)）。

关键成分（逐个由 13/14/15/16 号负对照隔离）：
`PY35 = PY3 and sys.version_info[1] >= 5` 是**值上下文 BoolOp**，其 merge 块
= `STORE PY35 | LOAD PY35 | POP_JUMP_IF_FALSE`，即下一条 `if PY35:` 的条件头块。
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
        line_profiler_py35 = None
    else:
        def is_coroutine(f):
            return inspect.iscoroutinefunction(f)
        wrap_coroutine = line_profiler_py35.wrap_coroutine
if not PY35:
    def is_coroutine(func):
        return False
    def wrap_coroutine(func):
        return None

CO_GENERATOR = 32
