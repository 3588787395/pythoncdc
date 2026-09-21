# -*- coding: utf-8 -*-
# R22 负对照 09 —— 最普通的 if/else（两臂都是单条语句）。
#
# J1' 的两条前置条件恒为 True（same_loop）/ False（shared_rn），完全不进守卫。
# 本复现（<module>.f）：base=MATCH after=MATCH。类别 GUARD。
def f(a, flag):
    if flag:
        print(1)
    else:
        print(a)
