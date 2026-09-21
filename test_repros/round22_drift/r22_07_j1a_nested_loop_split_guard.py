# -*- coding: utf-8 -*-
# R22 负对照 07 —— 两层嵌套循环里的 if/else 两臂（(a) 命中但塌缩并非必需）。
#
# 外层 for、两臂各在/不在内层 for：与 01/02 的区别是 merge 由支配关系正常算出，
# R13c 站点根本不触发 → J1'(a) 必须保持沉默。
# 本复现（<module>.f）：base=MATCH after=MATCH。类别 GUARD。
def f(xs, ys, flag):
    for x in xs:
        if flag:
            for y in ys:
                print(y)
        else:
            print(x)
