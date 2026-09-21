# -*- coding: utf-8 -*-
# R22 锚点 15 —— J2' 操作数换成 CONTAINS_OP（`in` / `not in` 混合）。
#
# 任务书点名的 `not in` 变体：证明链首落点识别与比较算子无关。
# 本复现（<module>.f，orig=21）：base=MISMATCH decomp=13，after=MATCH。类别 FIX。
def f(x, xs, y, ys):
    if x not in xs and x > 0 or y in ys and y < 0:
        return 1
    return 0
