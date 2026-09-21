# -*- coding: utf-8 -*-
# R22 负对照 10 —— 臂尾裸 `return None` + 尾随语句（(b) 的两半都在，但无害）。
#
# merge 由 NCPD 正常算出（两臂汇到函数级隐式 return None），R13c 站点不触发，
# (b) 必须不改变任何结论 —— 这条是 (b) 的"过火下限"探针。
# 本复现（<module>.f）：base=MATCH after=MATCH。类别 GUARD。
def f(a):
    if a:
        return None
    print(a)
