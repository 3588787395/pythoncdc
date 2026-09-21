# -*- coding: utf-8 -*-
# R22 负对照 20 —— `elif A and B or C and D:` 测试位换成 elif。
#
# elif 链上第一个 and 链的链首前驱被 FORWARD_CONDITIONAL_JUMP_OPS 的既有
# elif 判据接走，J2' 站点不参与。本复现（<module>.f）：base=MATCH after=MATCH。
# 类别 GUARD（语料同形：market_time.pyc 的 elif 分支 base/after 同为 ok）。
def f(a, b, c, d):
    if a > 1:
        print(1)
    elif a and b or c and d:
        print(2)
    return 0
