# -*- coding: utf-8 -*-
# R22 负对照 34 —— 单分支 if + `else: pass`（CFG 里只有**一条**条件跳转指向 NOP）。
#
# 折叠结果两世界一致：J3' 是纯删除，不得改变已经正确的场景。
# 本复现（<module>.f）：base=MATCH after=MATCH。类别 GUARD。
def f(a):
    if a == 1:
        print(1)
    else:
        pass
    print('tail')
