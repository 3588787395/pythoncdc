# -*- coding: utf-8 -*-
"""R14-J 15 负对照：BoolOp 与 if 之间**再插一条赋值**（破坏「头块 == merge 块」）。

真实目标：site-packages/IQCommon/profiler_func.pyc `<module>`。
`b = a and 2` 之后插入 `q = 5`，则 if 头块变成
`STORE_NAME q | LOAD_NAME b | POP_JUMP_IF_FALSE …`，块归属仍是被截断后的
BoolOp merge 之外的块 ⇒ IfRegion 正常建立。
本形状同时是既有豁免 `_is_merge_with_guard_clause`
（region_analyzer.py:15892-15905，要求 merge 块里 value STORE **之后还有第二个 STORE**）
的边界：真实缺陷里 merge 块只有 `STORE b` + 完整的 if 测试，没有第二个 STORE，
所以该豁免不触发。

实测（严格尺子）：<module> **MATCH**。
"""
a = 1
b = a and 2
q = 5
if b:
    try:
        c = 1
    except ValueError:
        pass
