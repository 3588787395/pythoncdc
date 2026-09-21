# -*- coding: utf-8 -*-
# R22 残留 25 —— `while A and B or C and D:` 循环测试位：两世界 seq_len 21→3。
#
# 同一条 or-and 链挂在 LoopRegion 的 test 上时，塌缩点完全不在 J2' 站点
# （−18，整条链连同循环体一起丢）。这是 J2' 覆盖面之外的循环侧根因，
# 与任务书点名的 "if-sink inside a while" 族同源。类别 RESIDUE。
def f(a, b, c, d):
    while a and b or c and d:
        a = 0
    return a
