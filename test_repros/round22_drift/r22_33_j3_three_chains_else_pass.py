# -*- coding: utf-8 -*-
# R22 锚点 33 —— elif 链 + `else: pass` 之后再挂一条独立 if（区域边界三连）。
#
# 本复现（<module>.f，orig=33）：base=MISMATCH decomp=32，after=MATCH。类别 FIX。
def f(m, a, b):
    if m == 1:
        if a:
            print(1)
    elif m == 2:
        if b:
            print(2)
    else:
        pass
    if m == 3:
        print(3)
    return 0
