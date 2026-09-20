# -*- coding: utf-8 -*-
"""R14-J 13 负对照：把标志位赋值里的**短路 BoolOp 去掉**，其余一字不变。

真实目标：site-packages/IQCommon/profiler_func.pyc `<module>`。
唯一差异：`b = a and 2` → `b = 2`。
去掉 BoolOp 之后，if 头块不再是某个 BoolOpRegion 的 merge_block，
`_identify_conditional_regions` 不再走「块已被 boolop 占用」分支，
IfRegion 正常建立、try 正常成为子区域。

实测（严格尺子）：<module> **MATCH** ⇒ 本缺陷类的必要成分是
「上一条语句是值上下文短路 BoolOp，且 if 头块恰是它的 merge 块」，
而不是 try 区域本身（try 只是把缺失的 IfRegion 暴露成语义差异）。
"""
a = 1
b = 2
if b:
    try:
        c = 1
    except ValueError:
        pass
