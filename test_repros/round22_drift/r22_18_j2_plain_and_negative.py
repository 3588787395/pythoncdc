# -*- coding: utf-8 -*-
# R22 负对照 18 —— 任务书点名的必测负对照：纯 `A and B` test 必须照常重建。
#
# 链首块没有"前向条件跳进来"的纯前驱（它是语句的第一个块）→ J2' 守卫不命中，
# and 链照常归约为 BoolOp。若这条变成 MISMATCH，说明守卫过火。
# 本复现（<module>.f）：base=MATCH after=MATCH。类别 GUARD。
def f(a, b):
    if a and b:
        return 1
    return 0
