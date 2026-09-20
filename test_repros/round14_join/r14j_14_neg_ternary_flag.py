# -*- coding: utf-8 -*-
"""R14-J 14 负对照：把短路 BoolOp 换成**三元表达式**（同类双角色块，另一构造）。

真实目标：site-packages/IQCommon/profiler_func.pyc `<module>`。
`b = (2 if a else 3)` 与 `b = a and 2` 在 CFG 上产生**完全同构**的双角色块：
块 = `STORE_NAME b | LOAD_NAME b | POP_JUMP_FORWARD_IF_FALSE <if 假出口>`，
既上一条语句的值归并点（merge_block），又是下一条 `if` 的条件头块。
区别只在归属区域的类型：TernaryRegion vs BoolOpRegion。

实测（严格尺子）：<module> **MATCH**，且区域树里 IfRegion **确实被创建**（entry = ternary 的 merge 块）、
TryExceptRegion 正常挂成它的子区域（D:/Temp/r14join/tern.py 实测）。
⇒ 「if 头块 == 表达式区域 merge 块」这个场景在 Ternary 路径上有
  对应的双角色豁免（_ternary_if_cond_redirect / merge_context 判定，
  region_analyzer.py:15704 起；见 ANALYSIS.md 的 tern.py 区域树：
  TernaryRegion@0(merge=B16) 与 IfRegion@16(子区域 = TryExceptRegion@24) 共存），
  BoolOp 路径上只有两个更窄的豁免
  （15883 需 COMPARE_OP、15892 需第二个 STORE），因此被 15910 一刀切跳过。
  这是修复的正确参照实现。
"""
a = 1
b = (2 if a else 3)
if b:
    try:
        c = 1
    except ValueError:
        pass
