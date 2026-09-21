# -*- coding: utf-8 -*-
# R22 锚点 16 —— J2' 三支 or（`A and B or C and D or E and F`）。
#
# 链首的前向条件跳进来者仍是纯操作数块 → 拒绝重建；既有嵌套路径接手。
# 本复现（<module>.f，orig=17）：base=MISMATCH decomp=9，after=MATCH。类别 FIX。
def f(a, b, c, d, e, g):
    if a and b or c and d or e and g:
        return 1
    return 0
