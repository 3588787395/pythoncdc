# -*- coding: utf-8 -*-
"""R16-A 10 负对照：被抢入口的是 **WithRegion**（then 臂里 with 体首语句即 BoolOp）。

region_ast_generator.py:14073-14105 已有一段 `[R2-With]` 先例：预生成时发现子区域是
WithRegion 就**回滚**它被打的标记、改成把 with 整体重新生成并挂 anchor。
本项检验该豁免是否只管 With（⇒ Try/Loop 仍缺同款处理，是候选修复要补的口子）。

预测 MATCH（已有专门处理）；若 MISMATCH ⇒ `[R2-With]` 先例本身漏了这条支路。
"""


def check_with_in_then_arm(value, ctx):
    if isinstance(value, str):
        with ctx:
            valid = int(value) > 0 and int(value) < 100
        return valid
    return False
