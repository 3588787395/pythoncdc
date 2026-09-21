# -*- coding: utf-8 -*-
# R22 锚点 32 —— elif 各臂内是 and / or BoolOp 条件（J3' 与 J2' 站点同函数共存）。
#
# 单跑 mirror/j2p 修不好它、单跑 mirror/j3 修得好 → 两规则站点正交。
# 本复现（<module>.f，orig=33）：base=MISMATCH decomp=32，after=MATCH。类别 FIX。
def f(mode, a, b):
    if mode == 1:
        if a and b:
            print(1)
    elif mode == 2:
        if a or b:
            print(2)
    else:
        pass
    print('tail')
