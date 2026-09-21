# -*- coding: utf-8 -*-
# R22 锚点 31 —— `else: pass` 位于 for 循环体内（语句边界在回边附近）。
#
# V-L（回边）判据与 [A4/V-M] 判据的分工在这里可见：删掉后者后折叠照常正确，
# 说明回边保护由 V-L 承担。语料同族：common_func.pyc / flytools.pyc 的循环内过滤。
# 本复现（<module>.f，orig=30）：base=MISMATCH decomp=29，after=MATCH。类别 FIX。
def f(xs, mode):
    for x in xs:
        if mode == 1:
            print(1)
        elif mode == 2:
            print(2)
        else:
            pass
        print(x)
