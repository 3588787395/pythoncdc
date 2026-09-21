# -*- coding: utf-8 -*-
# R22 残留 26 —— `A or B and C`（左析取支单操作数 + 右 and 链）。
#
# 与 12 的差别只在左半没有 and 链；两世界 target_diff #2 POP_JUMP_IF_TRUE
# 终点 orig=('1','LOAD_CONST') decomp=('c','LOAD_FAST')。类别 RESIDUE。
def f(a, b, c):
    if a or b and c:
        return 1
    return 0
