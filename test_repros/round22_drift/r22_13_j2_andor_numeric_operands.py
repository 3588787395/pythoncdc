# -*- coding: utf-8 -*-
# R22 锚点 13 —— J2' 把字符串比较换成数值参数（证明规则不看常量）。
#
# 本复现（<module>.f，orig=21）：base=MISMATCH decomp=13，after=MATCH。类别 FIX。
def f(v, lo, hi, lo2, hi2):
    if v >= lo and v <= hi or v >= lo2 and v <= hi2:
        return True
    return False
