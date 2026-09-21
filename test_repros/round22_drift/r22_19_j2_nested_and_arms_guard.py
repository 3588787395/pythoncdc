# -*- coding: utf-8 -*-
# R22 负对照 19 —— 嵌套 if 的两个 and test（内层链首的外层前驱是**结构**跳转）。
#
# 外层 `if a and b:` 的臂尾条件跳转落在内层链首之前，不满足
# `_pl.argval == _head.start_offset`（落点是内层 if 的语句序列头，而非纯操作数块）
# → 守卫不命中。本复现（<module>.f）：base=MATCH after=MATCH。类别 GUARD。
def f(a, b, c, d):
    if a and b:
        if c and d:
            return 1
    return 0
