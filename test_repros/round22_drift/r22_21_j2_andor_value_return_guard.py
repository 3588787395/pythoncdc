# -*- coding: utf-8 -*-
# R22 负对照 21 —— 值上下文（`return A and B or C and D`）。
#
# 值上下文走 BoolOpRegion 生成路径，不经 _discover_predicate_and_chain 的
# test 重建兜底 → J2' 无关。本复现：base=MATCH after=MATCH。类别 GUARD。
def f(a, b, c, d):
    return a and b or c and d
