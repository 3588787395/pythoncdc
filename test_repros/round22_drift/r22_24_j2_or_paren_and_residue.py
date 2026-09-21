# -*- coding: utf-8 -*-
# R22 残留 24 —— `A or (B and C)`（显式括号）：两世界 target_diff #2。
#
# 说明 J2' 修复的是**无括号**短路形态；带括号时链首前驱是
# POP_JUMP_FORWARD_IF_TRUE(短路 OR) 而非纯操作数块，守卫不命中，缺陷另有根因。
# 类别 RESIDUE。
def f(a, b, c):
    if a or (b and c):
        return 1
    return 0
