# -*- coding: utf-8 -*-
# R22 负对照 35 —— `while False: pass`（[A4/V-M] 子句 docstring 点名的保护对象）。
#
# 该方法 docstring 说"保持原有 while False: pass 还原"：删掉子句后这条必须仍是
# MATCH（真折叠残留 vs 语句边界锚点的判别由 V-B/V-L/exception_table 三半承担）。
# 本复现（<module>.f）：base=MATCH after=MATCH。类别 GUARD。
def f(a):
    if a:
        while False:
            pass
    print(a)
