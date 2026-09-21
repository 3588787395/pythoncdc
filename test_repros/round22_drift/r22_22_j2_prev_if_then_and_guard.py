# -*- coding: utf-8 -*-
# R22 负对照 22 —— J2' 过火下限探针：链首前驱是**上一条语句**的纯条件跳转。
#
# `if x: pass` 的条件块是纯块（无 STORE_*/POP_TOP），其
# POP_JUMP_FORWARD_IF_FALSE 的落点正是下一条语句 `if a and b:` 的链首块 ——
# 这是 J2' 字面判据唯一能被误用的入口。实测该形状两个世界都 MATCH：
# 兜底路径 `_discover_predicate_and_chain` 在此根本不参与（and 链由既有
# BoolOp 路径完整归约），守卫"不命中即无副作用"。
# 本复现（<module>.f）：base=MATCH after=MATCH。类别 GUARD。
def f(x, a, b):
    if x:
        pass
    if a and b:
        print(1)
