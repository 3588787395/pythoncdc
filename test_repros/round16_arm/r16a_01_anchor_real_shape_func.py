# -*- coding: utf-8 -*-
"""R16-A 01 锚点：`_is_valid_quarter` 的 1:1 真实形状（函数作用域）。

真实目标：site-packages/IQCommon/arg_checker.pyc
`<module>.ArgumentChecker._is_valid_quarter`，实测 orig=90 decomp=74（seq_len）。

与 round15 的 r15a_01 的区别：r15a_01 的 try 体是**单条链式比较**
（`1990 <= int(v) <= 9999`，只生成 TernaryRegion），症状是整条 if 丢失；
本复现的 try 体是**顶层 `and` + 两个链式比较**（与线上真实代码同形），
症状是 if/臂/守卫/else 全在，唯独 try 外壳与 except 处理块整体蒸发（少 16 条）。

假设（待实测）：BoolOpRegion@<try 入口> 与 TryExceptRegion@<同一入口> 是同一个
IfRegion 的兄弟 children；_if_generate_then_branch 的表达式子区域预生成先把该入口
块标记为 generated ⇒ _try_entry_generate 的 `if b in self.generated_blocks: continue`
空转 ⇒ try 丢失。
"""


def check_quarter(value):
    if value is None:
        valid = True
    else:
        valid = isinstance(value, str) and len(value) == 5
        if valid:
            try:
                valid = 1990 <= int(value) <= 9999 and 1 <= int(value) <= 4
            except (ValueError, TypeError):
                valid = False
    if not valid:
        raise ValueError(value)
    return valid
