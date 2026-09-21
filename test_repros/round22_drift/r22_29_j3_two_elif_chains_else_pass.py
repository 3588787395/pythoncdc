# -*- coding: utf-8 -*-
# R22 锚点 29 —— 两条 elif 链各带 `else: pass`（whitelist_filter 的双站点原形）。
#
# 第二条链的 `else: pass` 落点同样被第一条链的条件跳转"跨区污染"——这正是
# [A4/V-M] 子句被删的理由。语料同形锚点：flytools.pyc <module>.whitelist_filter
# 的 pack_filter_mode / cmd_filter_mode 两段。
# 本复现（<module>.f，orig=53）：base=MISMATCH decomp=52，after=MATCH。类别 FIX。
def f(mode, a, b):
    if mode == 1:
        if a:
            print(1)
    elif mode == 2:
        if b:
            print(2)
    else:
        pass
    if mode == 3:
        if a:
            print(3)
    elif mode == 4:
        if b:
            print(4)
    else:
        pass
