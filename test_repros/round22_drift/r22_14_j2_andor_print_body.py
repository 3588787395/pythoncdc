# -*- coding: utf-8 -*-
# R22 锚点 14 —— J2' 最小可能形：四个布尔名 + print 语句体。
#
# 本复现（<module>.f，orig=15）：base=MISMATCH decomp=11，after=MATCH。类别 FIX。
def f(a, b, c, d):
    if a and b or c and d:
        print(1)
    return 0
