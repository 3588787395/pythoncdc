# -*- coding: utf-8 -*-
# R22 锚点 17 —— J2' + 双臂各有若干语句（else 侧回归父序列的形态）。
#
# 本复现（<module>.f，orig=23）：base=MISMATCH decomp=19，after=MATCH。类别 FIX。
def f(a, b, c, d, e):
    if a and b or c and d:
        print(1)
        print(2)
    print(e)
